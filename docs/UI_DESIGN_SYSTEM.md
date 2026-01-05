# # UI_DESIGN_SYSTEM.md — Visual Interface Contract

**Document Type:** Reference
**Version:** 1.0.0
**Last Updated:** 2026-01-01
**Status:** Template
**Dependencies:** CODEBASECONSTITUTION.md §2, §5.

<meta_context>
**Non-Coder Executive Summary:** This is the "Style Guide." It stops the AI from using 50 different shades of blue or making buttons look different on every page. It forces the AI to use specific, pre-built "Lego blocks" so the app looks professional and consistent across the entire project.
</meta_context>

---

### 1. THE "NO RAW CSS" RULE
* **Rule:** You must NOT write raw CSS or arbitrary utility classes (e.g., hardcoded hex codes like `bg-[#123456]`).
* **Requirement:** You MUST use the standardized components in `core/ui/` or defined global design tokens.

---

### 2. CORE COMPONENTS (The "Lego" Box)
*AI: Always check `core/ui/` before building a new UI element.*

| Component | Intended Usage | Requirement |
| :--- | :--- | :--- |
| **Primary Button** | Main actions (Save, Book, Submit) | Use `core/ui/Button` |
| **Input Fields** | All user data entry | Use `core/ui/Input` |
| **Card / Container** | Grouping related content | Use `core/ui/Card` |
| **Typography** | All headings and body text | Use `core/ui/Text` |

---

### 3. DESIGN TOKENS (Tailwind/CSS Variables)
* **Primary Color:** Use `primary` (consistent branding).
* **Background:** Use `background` (standard canvas color).
* **Spacing:** Use a consistent 4px or 8px grid (e.g., `p-4`, `m-8`).

---

### 4. ACCESSIBILITY & RESPONSIVENESS
* **Mobile First:** All layouts must be verified on small screen sizes first.
* **Aria Labels:** All interactive elements must have descriptive labels for screen readers.
* **Contrast:** Ensure text color meets WCAG AA standards against backgrounds.
