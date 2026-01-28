"""
Contact and Company Data Enrichment Services.

Integrates with Clearbit, ZoomInfo, and LinkedIn to enrich contact
and company data automatically.

All services follow TIER 0 multi-tenancy requirements.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from modules.crm.models import (
    ContactEnrichment,
    EnrichmentProvider,
    EnrichmentQualityMetric,
)

logger = logging.getLogger(__name__)


class BaseEnrichmentService:
    """
    Base class for all enrichment services.

    Provides common functionality for API calls, error handling,
    and quality tracking.
    """

    def __init__(self, provider: EnrichmentProvider):
        """Initialize service with provider configuration."""
        self.provider = provider
        self.api_key = provider.api_key
        self.api_secret = provider.api_secret
        self.config = provider.additional_config or {}
        self.timeout = self.config.get("timeout", 30)  # seconds

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Make HTTP request to enrichment API.

        Returns:
            Tuple of (response_data, error_message)
        """
        start_time = time.time()

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=self.timeout,
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                logger.info(
                    f"{self.provider.provider} API success: {url} "
                    f"({response_time_ms}ms)"
                )
                return response.json(), None

            elif response.status_code == 404:
                logger.warning(f"{self.provider.provider} API: Not found - {url}")
                return None, "not_found"

            elif response.status_code == 429:
                logger.warning(f"{self.provider.provider} API: Rate limit exceeded")
                return None, "rate_limit"

            elif response.status_code == 401:
                logger.error(f"{self.provider.provider} API: Unauthorized")
                return None, "unauthorized"

            else:
                logger.error(
                    f"{self.provider.provider} API error {response.status_code}: "
                    f"{response.text}"
                )
                return None, f"http_{response.status_code}"

        except requests.exceptions.Timeout:
            logger.error(f"{self.provider.provider} API timeout after {self.timeout}s")
            return None, "timeout"

        except requests.exceptions.RequestException as e:
            logger.error(f"{self.provider.provider} API request failed: {e}")
            return None, "connection_error"

        except Exception as e:
            logger.error(
                f"{self.provider.provider} API unexpected error: {e}",
                exc_info=True
            )
            return None, "unknown_error"

    def _update_provider_stats(self, success: bool):
        """Update provider usage statistics."""
        self.provider.total_enrichments += 1
        if success:
            self.provider.successful_enrichments += 1
        else:
            self.provider.failed_enrichments += 1
        self.provider.last_used_at = timezone.now()
        self.provider.save(
            update_fields=[
                "total_enrichments",
                "successful_enrichments",
                "failed_enrichments",
                "last_used_at",
                "updated_at",
            ]
        )

    def _track_quality_metric(
        self,
        success: bool,
        fields_enriched: List[str],
        response_time_ms: int,
        error_type: Optional[str] = None,
    ):
        """Track quality metrics for this enrichment."""
        today = timezone.now().date()

        metric, created = EnrichmentQualityMetric.objects.get_or_create(
            enrichment_provider=self.provider,
            metric_date=today,
        )

        metric.total_enrichments += 1
        if success:
            metric.successful_enrichments += 1
        else:
            metric.failed_enrichments += 1

        # Update average response time
        if metric.average_response_time_ms == 0:
            metric.average_response_time_ms = response_time_ms
        else:
            # Rolling average
            total = metric.total_enrichments
            metric.average_response_time_ms = int(
                (metric.average_response_time_ms * (total - 1) + response_time_ms) / total
            )

        # Track field success rates
        if success and fields_enriched:
            field_rates = metric.field_success_rates or {}
            for field in fields_enriched:
                if field not in field_rates:
                    field_rates[field] = {"success": 0, "total": 0}
                field_rates[field]["success"] += 1
                field_rates[field]["total"] += 1
            metric.field_success_rates = field_rates

        # Track error types
        if error_type:
            error_types = metric.error_types or {}
            error_types[error_type] = error_types.get(error_type, 0) + 1
            metric.error_types = error_types

        metric.save()


class ClearbitEnrichmentService(BaseEnrichmentService):
    """
    Clearbit enrichment service.

    Enriches contacts and companies using Clearbit's Enrichment API.
    https://clearbit.com/docs#enrichment-api
    """

    BASE_URL = "https://person.clearbit.com/v2"
    COMPANY_URL = "https://company.clearbit.com/v2"

    def enrich_contact(
        self,
        email: str,
        contact: Optional['AccountContact'] = None,
        client_contact: Optional['Contact'] = None,
    ) -> Tuple[Optional[ContactEnrichment], Optional[str]]:
        """
        Enrich contact using email address.

        Args:
            email: Contact's email address
            contact: AccountContact instance (CRM contact)
            client_contact: Contact instance (Client contact)

        Returns:
            Tuple of (ContactEnrichment instance or None, error_message)
        """
        start_time = time.time()

        # Get person data
        person_url = f"{self.BASE_URL}/combined/find"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"email": email}

        data, error = self._make_request("GET", person_url, headers=headers, params=params)
        response_time_ms = int((time.time() - start_time) * 1000)

        if error:
            self._update_provider_stats(success=False)
            self._track_quality_metric(
                success=False,
                fields_enriched=[],
                response_time_ms=response_time_ms,
                error_type=error,
            )
            return None, error

        if not data:
            self._update_provider_stats(success=False)
            return None, "no_data"

        # Extract enrichment data
        enrichment_data = self._extract_clearbit_data(data)

        # Create or update ContactEnrichment
        enrichment = self._save_enrichment(
            contact=contact,
            client_contact=client_contact,
            enrichment_data=enrichment_data,
            raw_data=data,
        )

        self._update_provider_stats(success=True)
        self._track_quality_metric(
            success=True,
            fields_enriched=enrichment_data["fields_enriched"],
            response_time_ms=response_time_ms,
        )

        return enrichment, None

    def _extract_clearbit_data(self, data: Dict) -> Dict:
        """Extract relevant data from Clearbit response."""
        person = data.get("person", {})
        company = data.get("company", {})

        fields_enriched = []
        fields_missing = []

        # Company data
        company_name = company.get("name", "")
        if company_name:
            fields_enriched.append("company_name")
        else:
            fields_missing.append("company_name")

        company_domain = company.get("domain", "")
        if company_domain:
            fields_enriched.append("company_domain")
        else:
            fields_missing.append("company_domain")

        company_industry = company.get("category", {}).get("industry", "")
        if company_industry:
            fields_enriched.append("company_industry")
        else:
            fields_missing.append("company_industry")

        # Employee count range
        metrics = company.get("metrics", {})
        employees = metrics.get("employees")
        company_size = f"{employees}" if employees else ""
        if company_size:
            fields_enriched.append("company_size")
        else:
            fields_missing.append("company_size")

        # Revenue range
        annual_revenue = metrics.get("annualRevenue")
        company_revenue = f"${annual_revenue:,}" if annual_revenue else ""
        if company_revenue:
            fields_enriched.append("company_revenue")
        else:
            fields_missing.append("company_revenue")

        company_description = company.get("description", "")
        if company_description:
            fields_enriched.append("company_description")

        company_logo_url = company.get("logo", "")
        if company_logo_url:
            fields_enriched.append("company_logo_url")

        # Location
        geo = company.get("geo", {})
        city = geo.get("city", "")
        state = geo.get("state", "")
        country = geo.get("country", "")
        location_parts = [p for p in [city, state, country] if p]
        company_location = ", ".join(location_parts)
        if company_location:
            fields_enriched.append("company_location")

        company_founded_year = company.get("foundedYear")
        if company_founded_year:
            fields_enriched.append("company_founded_year")

        # Contact data
        employment = person.get("employment", {})
        contact_title = employment.get("title", "")
        if contact_title:
            fields_enriched.append("contact_title")

        contact_seniority = employment.get("seniority", "")
        if contact_seniority:
            fields_enriched.append("contact_seniority")

        contact_role = employment.get("role", "")
        if contact_role:
            fields_enriched.append("contact_role")

        # Social profiles
        linkedin_url = person.get("linkedin", {}).get("handle", "")
        if linkedin_url and not linkedin_url.startswith("http"):
            linkedin_url = f"https://linkedin.com/in/{linkedin_url}"
        if linkedin_url:
            fields_enriched.append("linkedin_url")

        twitter_url = person.get("twitter", {}).get("handle", "")
        if twitter_url and not twitter_url.startswith("http"):
            twitter_url = f"https://twitter.com/{twitter_url}"
        if twitter_url:
            fields_enriched.append("twitter_url")

        facebook_url = person.get("facebook", {}).get("handle", "")
        if facebook_url and not facebook_url.startswith("http"):
            facebook_url = f"https://facebook.com/{facebook_url}"
        if facebook_url:
            fields_enriched.append("facebook_url")

        github_url = person.get("github", {}).get("handle", "")
        if github_url and not github_url.startswith("http"):
            github_url = f"https://github.com/{github_url}"
        if github_url:
            fields_enriched.append("github_url")

        # Technologies
        technologies = company.get("tech", []) or []
        if technologies:
            fields_enriched.append("technologies")

        # Calculate confidence score (Clearbit provides fuzzy flag)
        fuzzy = data.get("fuzzy", False)
        confidence_score = 70.0 if fuzzy else 95.0

        return {
            "company_name": company_name,
            "company_domain": company_domain,
            "company_industry": company_industry,
            "company_size": company_size,
            "company_revenue": company_revenue,
            "company_description": company_description,
            "company_logo_url": company_logo_url,
            "company_location": company_location,
            "company_founded_year": company_founded_year,
            "contact_title": contact_title,
            "contact_seniority": contact_seniority,
            "contact_role": contact_role,
            "linkedin_url": linkedin_url,
            "twitter_url": twitter_url,
            "facebook_url": facebook_url,
            "github_url": github_url,
            "technologies": technologies,
            "confidence_score": confidence_score,
            "fields_enriched": fields_enriched,
            "fields_missing": fields_missing,
        }

    def _save_enrichment(
        self,
        contact,
        client_contact,
        enrichment_data: Dict,
        raw_data: Dict,
    ) -> ContactEnrichment:
        """Save or update ContactEnrichment record."""
        # Check if enrichment already exists
        if contact:
            enrichment, created = ContactEnrichment.objects.get_or_create(
                account_contact=contact,
                defaults={"enrichment_provider": self.provider}
            )
        elif client_contact:
            enrichment, created = ContactEnrichment.objects.get_or_create(
                client_contact=client_contact,
                defaults={"enrichment_provider": self.provider}
            )
        else:
            raise ValueError("Either contact or client_contact must be provided")

        # Update enrichment data
        enrichment.company_name = enrichment_data["company_name"]
        enrichment.company_domain = enrichment_data["company_domain"]
        enrichment.company_industry = enrichment_data["company_industry"]
        enrichment.company_size = enrichment_data["company_size"]
        enrichment.company_revenue = enrichment_data["company_revenue"]
        enrichment.company_description = enrichment_data["company_description"]
        enrichment.company_logo_url = enrichment_data["company_logo_url"]
        enrichment.company_location = enrichment_data["company_location"]
        enrichment.company_founded_year = enrichment_data["company_founded_year"]
        enrichment.contact_title = enrichment_data["contact_title"]
        enrichment.contact_seniority = enrichment_data["contact_seniority"]
        enrichment.contact_role = enrichment_data["contact_role"]
        enrichment.linkedin_url = enrichment_data["linkedin_url"]
        enrichment.twitter_url = enrichment_data["twitter_url"]
        enrichment.facebook_url = enrichment_data["facebook_url"]
        enrichment.github_url = enrichment_data["github_url"]
        enrichment.technologies = enrichment_data["technologies"]
        enrichment.confidence_score = enrichment_data["confidence_score"]
        enrichment.fields_enriched = enrichment_data["fields_enriched"]
        enrichment.fields_missing = enrichment_data["fields_missing"]
        enrichment.raw_data = raw_data
        enrichment.last_enriched_at = timezone.now()
        enrichment.is_stale = False
        enrichment.enrichment_error = ""

        if not created:
            enrichment.refresh_count += 1

        # Calculate next refresh time
        enrichment.calculate_next_refresh()

        enrichment.save()

        return enrichment


class ZoomInfoEnrichmentService(BaseEnrichmentService):
    """
    ZoomInfo enrichment service.

    Enriches contacts and companies using ZoomInfo's API.
    https://api-docs.zoominfo.com/
    """

    BASE_URL = "https://api.zoominfo.com"

    def enrich_contact(
        self,
        email: str,
        contact: Optional['AccountContact'] = None,
        client_contact: Optional['Contact'] = None,
    ) -> Tuple[Optional[ContactEnrichment], Optional[str]]:
        """
        Enrich contact using email address.

        Args:
            email: Contact's email address
            contact: AccountContact instance (CRM contact)
            client_contact: Contact instance (Client contact)

        Returns:
            Tuple of (ContactEnrichment instance or None, error_message)
        """
        start_time = time.time()

        # Get access token first
        access_token, token_error = self._get_access_token()
        if token_error:
            return None, token_error

        # Search for contact by email
        search_url = f"{self.BASE_URL}/lookup/contact"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        json_data = {"emailAddress": email}

        data, error = self._make_request(
            "POST", search_url, headers=headers, json_data=json_data
        )
        response_time_ms = int((time.time() - start_time) * 1000)

        if error:
            self._update_provider_stats(success=False)
            self._track_quality_metric(
                success=False,
                fields_enriched=[],
                response_time_ms=response_time_ms,
                error_type=error,
            )
            return None, error

        if not data or not data.get("data"):
            self._update_provider_stats(success=False)
            return None, "no_data"

        # Extract enrichment data
        contact_data = data["data"][0] if isinstance(data["data"], list) else data["data"]
        enrichment_data = self._extract_zoominfo_data(contact_data)

        # Create or update ContactEnrichment
        enrichment = self._save_enrichment(
            contact=contact,
            client_contact=client_contact,
            enrichment_data=enrichment_data,
            raw_data=data,
        )

        self._update_provider_stats(success=True)
        self._track_quality_metric(
            success=True,
            fields_enriched=enrichment_data["fields_enriched"],
            response_time_ms=response_time_ms,
        )

        return enrichment, None

    def _get_access_token(self) -> Tuple[Optional[str], Optional[str]]:
        """Get OAuth access token for ZoomInfo API."""
        # Check if we have a cached token
        cached_token = self.config.get("access_token")
        token_expires_at = self.config.get("token_expires_at")

        if cached_token and token_expires_at:
            from datetime import datetime
            expires_at = datetime.fromisoformat(token_expires_at)
            if expires_at > timezone.now():
                return cached_token, None

        # Request new token
        token_url = f"{self.BASE_URL}/authenticate"
        headers = {"Content-Type": "application/json"}
        json_data = {
            "username": self.config.get("username"),
            "password": self.api_secret,
        }

        data, error = self._make_request(
            "POST", token_url, headers=headers, json_data=json_data
        )

        if error:
            return None, f"auth_error: {error}"

        if not data or "access_token" not in data:
            return None, "auth_error: no token"

        # Cache the token
        access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)  # Default 1 hour
        token_expires_at = timezone.now() + timedelta(seconds=expires_in)

        self.config["access_token"] = access_token
        self.config["token_expires_at"] = token_expires_at.isoformat()
        self.provider.additional_config = self.config
        self.provider.save(update_fields=["additional_config", "updated_at"])

        return access_token, None

    def _extract_zoominfo_data(self, data: Dict) -> Dict:
        """Extract relevant data from ZoomInfo response."""
        fields_enriched = []
        fields_missing = []

        # Company data
        company = data.get("company", {})

        company_name = company.get("companyName", "")
        if company_name:
            fields_enriched.append("company_name")
        else:
            fields_missing.append("company_name")

        company_domain = company.get("website", "")
        if company_domain:
            fields_enriched.append("company_domain")
        else:
            fields_missing.append("company_domain")

        company_industry = company.get("industry", "")
        if company_industry:
            fields_enriched.append("company_industry")
        else:
            fields_missing.append("company_industry")

        company_size = str(company.get("employeeCount", ""))
        if company_size:
            fields_enriched.append("company_size")
        else:
            fields_missing.append("company_size")

        revenue = company.get("revenue")
        company_revenue = f"${revenue:,}" if revenue else ""
        if company_revenue:
            fields_enriched.append("company_revenue")

        company_description = company.get("companyDescription", "")
        if company_description:
            fields_enriched.append("company_description")

        # Location
        city = company.get("city", "")
        state = company.get("state", "")
        country = company.get("country", "")
        location_parts = [p for p in [city, state, country] if p]
        company_location = ", ".join(location_parts)
        if company_location:
            fields_enriched.append("company_location")

        # Contact data
        contact_title = data.get("jobTitle", "")
        if contact_title:
            fields_enriched.append("contact_title")

        contact_seniority = data.get("managementLevel", "")
        if contact_seniority:
            fields_enriched.append("contact_seniority")

        contact_role = data.get("jobFunction", "")
        if contact_role:
            fields_enriched.append("contact_role")

        # Social profiles
        linkedin_url = data.get("linkedInUrl", "")
        if linkedin_url:
            fields_enriched.append("linkedin_url")

        # Confidence score (ZoomInfo provides accuracy indicators)
        confidence_score = data.get("confidenceScore", 85.0)

        return {
            "company_name": company_name,
            "company_domain": company_domain,
            "company_industry": company_industry,
            "company_size": company_size,
            "company_revenue": company_revenue,
            "company_description": company_description,
            "company_logo_url": "",  # ZoomInfo doesn't provide logos
            "company_location": company_location,
            "company_founded_year": None,
            "contact_title": contact_title,
            "contact_seniority": contact_seniority,
            "contact_role": contact_role,
            "linkedin_url": linkedin_url,
            "twitter_url": "",
            "facebook_url": "",
            "github_url": "",
            "technologies": [],
            "confidence_score": confidence_score,
            "fields_enriched": fields_enriched,
            "fields_missing": fields_missing,
        }

    def _save_enrichment(
        self,
        contact,
        client_contact,
        enrichment_data: Dict,
        raw_data: Dict,
    ) -> ContactEnrichment:
        """Save or update ContactEnrichment record."""
        # Reuse Clearbit's save method (same logic)
        clearbit_service = ClearbitEnrichmentService(self.provider)
        return clearbit_service._save_enrichment(
            contact, client_contact, enrichment_data, raw_data
        )


class LinkedInEnrichmentService(BaseEnrichmentService):
    """
    LinkedIn enrichment service.

    Enriches contacts with LinkedIn profile data.
    Note: This uses LinkedIn's official API which requires OAuth.
    """

    BASE_URL = "https://api.linkedin.com/v2"

    def enrich_contact_by_url(
        self,
        linkedin_url: str,
        contact: Optional['AccountContact'] = None,
        client_contact: Optional['Contact'] = None,
    ) -> Tuple[Optional[ContactEnrichment], Optional[str]]:
        """
        Enrich contact using LinkedIn profile URL.

        Args:
            linkedin_url: LinkedIn profile URL
            contact: AccountContact instance (CRM contact)
            client_contact: Contact instance (Client contact)

        Returns:
            Tuple of (ContactEnrichment instance or None, error_message)
        """
        # Extract profile ID from URL
        profile_id = self._extract_profile_id(linkedin_url)
        if not profile_id:
            return None, "invalid_url"

        start_time = time.time()

        # Get profile data
        profile_url = f"{self.BASE_URL}/people/({profile_id})"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        data, error = self._make_request("GET", profile_url, headers=headers)
        response_time_ms = int((time.time() - start_time) * 1000)

        if error:
            self._update_provider_stats(success=False)
            self._track_quality_metric(
                success=False,
                fields_enriched=[],
                response_time_ms=response_time_ms,
                error_type=error,
            )
            return None, error

        if not data:
            self._update_provider_stats(success=False)
            return None, "no_data"

        # Extract enrichment data
        enrichment_data = self._extract_linkedin_data(data, linkedin_url)

        # Update existing enrichment or create new one
        if contact:
            enrichment, created = ContactEnrichment.objects.get_or_create(
                account_contact=contact,
                defaults={"enrichment_provider": self.provider}
            )
        elif client_contact:
            enrichment, created = ContactEnrichment.objects.get_or_create(
                client_contact=client_contact,
                defaults={"enrichment_provider": self.provider}
            )
        else:
            raise ValueError("Either contact or client_contact must be provided")

        # Update only LinkedIn-specific fields
        enrichment.linkedin_url = linkedin_url
        enrichment.contact_title = enrichment_data.get("contact_title", enrichment.contact_title)

        # Merge fields_enriched
        existing_fields = set(enrichment.fields_enriched or [])
        new_fields = set(enrichment_data["fields_enriched"])
        enrichment.fields_enriched = list(existing_fields | new_fields)

        enrichment.raw_data["linkedin"] = data
        enrichment.last_enriched_at = timezone.now()
        enrichment.save()

        self._update_provider_stats(success=True)
        self._track_quality_metric(
            success=True,
            fields_enriched=enrichment_data["fields_enriched"],
            response_time_ms=response_time_ms,
        )

        return enrichment, None

    def _extract_profile_id(self, linkedin_url: str) -> Optional[str]:
        """Extract profile ID from LinkedIn URL."""
        # Example: https://linkedin.com/in/johndoe → johndoe
        import re
        match = re.search(r"linkedin\.com/in/([^/\?]+)", linkedin_url)
        if match:
            return match.group(1)
        return None

    def _extract_linkedin_data(self, data: Dict, linkedin_url: str) -> Dict:
        """Extract relevant data from LinkedIn response."""
        fields_enriched = ["linkedin_url"]

        # LinkedIn API provides limited data due to privacy
        # This is a simplified extraction
        contact_title = ""
        positions = data.get("positions", {}).get("values", [])
        if positions:
            contact_title = positions[0].get("title", "")
            if contact_title:
                fields_enriched.append("contact_title")

        return {
            "contact_title": contact_title,
            "fields_enriched": fields_enriched,
        }


class EnrichmentOrchestrator:
    """
    Orchestrates enrichment across multiple providers.

    Manages priority, fallbacks, and merging data from multiple sources.
    """

    def __init__(self, firm):
        """Initialize orchestrator with firm context."""
        self.firm = firm

    def enrich_contact(
        self,
        email: str,
        contact: Optional['AccountContact'] = None,
        client_contact: Optional['Contact'] = None,
        providers: Optional[List[str]] = None,
    ) -> Tuple[Optional[ContactEnrichment], List[str]]:
        """
        Enrich contact using one or more providers.

        Args:
            email: Contact's email address
            contact: AccountContact instance (CRM contact)
            client_contact: Contact instance (Client contact)
            providers: List of provider names to use (or None for all enabled)

        Returns:
            Tuple of (ContactEnrichment instance or None, list of errors)
        """
        errors = []
        enrichment = None

        # Get enabled providers for this firm
        enabled_providers = EnrichmentProvider.objects.filter(
            firm=self.firm,
            is_enabled=True,
        )

        if providers:
            enabled_providers = enabled_providers.filter(provider__in=providers)

        # Try each provider in order
        for provider in enabled_providers:
            try:
                if provider.provider == "clearbit":
                    service = ClearbitEnrichmentService(provider)
                    enrichment, error = service.enrich_contact(
                        email, contact, client_contact
                    )

                elif provider.provider == "zoominfo":
                    service = ZoomInfoEnrichmentService(provider)
                    enrichment, error = service.enrich_contact(
                        email, contact, client_contact
                    )

                else:
                    error = f"unsupported_provider: {provider.provider}"

                if error:
                    errors.append(f"{provider.provider}: {error}")

                # If we got enrichment data, we're done
                if enrichment:
                    logger.info(
                        f"Successfully enriched {email} using {provider.provider}"
                    )
                    break

            except Exception as e:
                logger.error(
                    f"Enrichment failed for {email} using {provider.provider}: {e}",
                    exc_info=True
                )
                errors.append(f"{provider.provider}: {str(e)}")

        return enrichment, errors

    def enrich_linkedin_profile(
        self,
        linkedin_url: str,
        contact: Optional['AccountContact'] = None,
        client_contact: Optional['Contact'] = None,
    ) -> Tuple[Optional[ContactEnrichment], Optional[str]]:
        """
        Enrich contact using LinkedIn profile URL.

        Args:
            linkedin_url: LinkedIn profile URL
            contact: AccountContact instance (CRM contact)
            client_contact: Contact instance (Client contact)

        Returns:
            Tuple of (ContactEnrichment instance or None, error_message)
        """
        # Get LinkedIn provider
        try:
            provider = EnrichmentProvider.objects.get(
                firm=self.firm,
                provider="linkedin",
                is_enabled=True,
            )
        except EnrichmentProvider.DoesNotExist:
            return None, "linkedin_provider_not_configured"

        service = LinkedInEnrichmentService(provider)
        return service.enrich_contact_by_url(linkedin_url, contact, client_contact)
