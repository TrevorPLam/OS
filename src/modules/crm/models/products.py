from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


class Product(models.Model):
    """
    Product model for CPQ system (Task 3.5).
    
    Represents a product or service that can be configured and quoted.
    Products can be simple (no configuration) or complex (multiple options).
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    PRODUCT_TYPE_CHOICES = [
        ("service", "Service"),
        ("product", "Product"),
        ("subscription", "Subscription"),
        ("bundle", "Bundle"),
    ]
    
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("archived", "Archived"),
    ]
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="cpq_products",
        help_text="Firm (workspace) this product belongs to"
    )
    
    # Product Identity
    code = models.CharField(
        max_length=100,
        help_text="Unique product code/SKU"
    )
    name = models.CharField(max_length=255, help_text="Product name")
    description = models.TextField(blank=True, help_text="Product description")
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default="service"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Base price before configuration"
    )
    currency = models.CharField(max_length=3, default="USD", help_text="Currency code (ISO 4217)")
    
    # Configuration
    is_configurable = models.BooleanField(
        default=False,
        help_text="Whether this product has configurable options"
    )
    configuration_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON schema defining configuration rules and dependencies"
    )
    
    # Metadata
    category = models.CharField(max_length=100, blank=True, help_text="Product category")
    tags = models.JSONField(default=list, blank=True, help_text="Product tags for filtering")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_products",
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "crm_product"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["firm", "status"], name="crm_prod_firm_status_idx"),
            models.Index(fields=["firm", "code"], name="crm_prod_firm_code_idx"),
            models.Index(fields=["firm", "product_type"], name="crm_prod_firm_type_idx"),
        ]
        unique_together = [["firm", "code"]]
    
    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class ProductOption(models.Model):
    """
    ProductOption model for CPQ system (Task 3.5).
    
    Represents a configurable option for a product (e.g., size, color, features).
    Options can affect pricing and have dependencies on other options.
    
    TIER 0: Inherits firm from product.
    """
    
    OPTION_TYPE_CHOICES = [
        ("single_select", "Single Select"),
        ("multi_select", "Multi Select"),
        ("text", "Text Input"),
        ("number", "Number Input"),
        ("boolean", "Boolean"),
    ]
    
    # Parent product
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="options",
        help_text="Product this option belongs to"
    )
    
    # Option Identity
    code = models.CharField(max_length=100, help_text="Option code")
    label = models.CharField(max_length=255, help_text="Display label")
    description = models.TextField(blank=True, help_text="Option description")
    option_type = models.CharField(
        max_length=20,
        choices=OPTION_TYPE_CHOICES,
        default="single_select"
    )
    
    # Configuration
    required = models.BooleanField(default=False, help_text="Whether this option is required")
    display_order = models.IntegerField(default=0, help_text="Display order in UI")
    
    # Values (for select options)
    values = models.JSONField(
        default=list,
        blank=True,
        help_text="Available values for select options: [{value, label, price_modifier}]"
    )
    
    # Pricing Impact
    price_modifier = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Fixed price modifier (added to base price)"
    )
    price_multiplier = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=Decimal("1.0000"),
        validators=[MinValueValidator(Decimal("0.0000"))],
        help_text="Price multiplier (applied to base price)"
    )
    
    # Dependencies and Rules
    dependency_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Rules defining when this option is available based on other options"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "crm_product_option"
        ordering = ["display_order", "label"]
        indexes = [
            models.Index(fields=["product", "display_order"], name="crm_prod_opt_prod_ord_idx"),
            models.Index(fields=["product", "code"], name="crm_prod_opt_prod_code_idx"),
        ]
        unique_together = [["product", "code"]]
    
    def __str__(self) -> str:
        return f"{self.product.code} - {self.label}"


class ProductConfiguration(models.Model):
    """
    ProductConfiguration model for CPQ system (Task 3.5).
    
    Represents a specific configuration of a product with selected options.
    Stores the configuration choices and calculated pricing.
    
    TIER 0: Inherits firm from product.
    """
    
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("validated", "Validated"),
        ("quoted", "Quoted"),
    ]
    
    # Product reference
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="configurations",
        help_text="Product being configured"
    )
    
    # Configuration Data
    configuration_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional name for this configuration"
    )
    selected_options = models.JSONField(
        default=dict,
        help_text="Selected options: {option_code: value}"
    )
    
    # Pricing Calculation
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Base price at time of configuration"
    )
    configuration_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total price after applying configuration"
    )
    price_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed price breakdown: {base, options, discounts, total}"
    )
    
    # Discount
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Discount percentage applied to configuration"
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Calculated discount amount"
    )
    
    # Validation
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        help_text="Validation errors if configuration is invalid"
    )
    
    # Quote Reference (if this configuration becomes a quote)
    quote = models.ForeignKey(
        "pricing.Quote",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_configurations",
        help_text="Quote created from this configuration"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_configurations",
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "crm_product_configuration"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "-created_at"], name="crm_prod_cfg_prod_cre_idx"),
            models.Index(fields=["product", "status"], name="crm_prod_cfg_prod_sta_idx"),
            models.Index(fields=["quote"], name="crm_prod_cfg_quote_idx"),
        ]
    
    def __str__(self) -> str:
        name = self.configuration_name or f"Configuration {self.pk}"
        return f"{self.product.code} - {name}"
    
    def calculate_price(self) -> Decimal:
        """
        Calculate the total price based on base price and selected options.
        
        Returns:
            Calculated configuration price
        """
        total_price = self.base_price
        option_adjustments = Decimal("0.00")
        multiplier = Decimal("1.0000")
        breakdown = {
            "base_price": float(self.base_price),
            "options": [],
            "subtotal": 0,
            "discount_percentage": float(self.discount_percentage),
            "discount_amount": 0,
            "total": 0,
        }
        
        # Apply option pricing
        for option_code, value in self.selected_options.items():
            try:
                option = self.product.options.get(code=option_code)
                
                # Apply fixed price modifier
                if option.price_modifier != Decimal("0.00"):
                    option_adjustments += option.price_modifier
                    breakdown["options"].append({
                        "option": option_code,
                        "label": option.label,
                        "type": "modifier",
                        "amount": float(option.price_modifier),
                    })
                
                # Apply price multiplier
                if option.price_multiplier != Decimal("1.0000"):
                    multiplier *= option.price_multiplier
                    breakdown["options"].append({
                        "option": option_code,
                        "label": option.label,
                        "type": "multiplier",
                        "amount": float(option.price_multiplier),
                    })
                
                # Check for value-specific pricing (in select options)
                if option.option_type in ["single_select", "multi_select"]:
                    for val_obj in option.values:
                        if val_obj.get("value") == value:
                            val_price = Decimal(str(val_obj.get("price_modifier", 0)))
                            if val_price != Decimal("0.00"):
                                option_adjustments += val_price
                                breakdown["options"].append({
                                    "option": option_code,
                                    "label": f"{option.label}: {val_obj.get('label', value)}",
                                    "type": "value_modifier",
                                    "amount": float(val_price),
                                })
            except ProductOption.DoesNotExist:
                pass
        
        # Calculate subtotal
        subtotal = (total_price + option_adjustments) * multiplier
        breakdown["subtotal"] = float(subtotal)
        
        # Apply discount
        discount_amount = subtotal * (self.discount_percentage / Decimal("100.00"))
        breakdown["discount_amount"] = float(discount_amount)
        self.discount_amount = discount_amount
        
        # Calculate final total
        final_total = subtotal - discount_amount
        breakdown["total"] = float(final_total)
        
        self.price_breakdown = breakdown
        return final_total
    
    def validate_configuration(self) -> tuple[bool, list[str]]:
        """
        Validate the configuration against product rules and dependencies.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check required options
        required_options = self.product.options.filter(required=True)
        for option in required_options:
            if option.code not in self.selected_options:
                errors.append(f"Required option '{option.label}' is missing")
        
        # Check option dependencies
        for option_code, value in self.selected_options.items():
            try:
                option = self.product.options.get(code=option_code)
                if option.dependency_rules:
                    # Evaluate dependency rules
                    dependencies_met = self._evaluate_dependencies(option.dependency_rules)
                    if not dependencies_met:
                        errors.append(
                            f"Option '{option.label}' dependencies not met: {option.dependency_rules}"
                        )
            except ProductOption.DoesNotExist:
                errors.append(f"Invalid option code: {option_code}")
        
        is_valid = len(errors) == 0
        self.validation_errors = errors
        self.status = "validated" if is_valid else "draft"
        
        return is_valid, errors
    
    def _evaluate_dependencies(self, rules: dict) -> bool:
        """
        Evaluate dependency rules against selected options.
        
        Args:
            rules: Dictionary of dependency rules
            
        Returns:
            True if dependencies are met, False otherwise
        """
        if not rules:
            return True
        
        # Simple implementation: check if required options are present
        required = rules.get("requires", [])
        for req in required:
            if isinstance(req, dict):
                option_code = req.get("option")
                required_value = req.get("value")
                if option_code not in self.selected_options:
                    return False
                if required_value and self.selected_options[option_code] != required_value:
                    return False
            elif isinstance(req, str):
                if req not in self.selected_options:
                    return False
        
        return True
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to calculate price before saving."""
        # Set base price from product if not set
        if not self.base_price:
            self.base_price = self.product.base_price
        
        # Calculate configuration price
        self.configuration_price = self.calculate_price()
        
        super().save(*args, **kwargs)


