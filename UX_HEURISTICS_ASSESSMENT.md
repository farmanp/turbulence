# UX Heuristics Assessment: Scenario Visualizer

## Overview
This assessment evaluates the current state of the **Scenario Visualizer** (FEAT-027) against Jakob Nielsen's 10 Usability Heuristics.

**Evaluated Components:**
- `ScenarioVisualizerPage.tsx`
- `ScenarioNode.tsx`
- `StepDetailPanel.tsx`
- `flowUtils.ts`

---

## Heuristic Analysis

### 1. Visibility of System Status
**Score: 3/5 (Acceptable)**
- **Positive:** Parse errors are shown immediately in a dedicated error panel.
- **Negative:** There is no visual feedback during the debounced parsing state (200ms). When pasting large YAMLs, the user might wonder if the system is frozen.
- **Recommendation:** Add a subtle "Syncing..." or "Parsing..." spinner in the editor header when `handleYamlChange` is active.

### 2. Match Between System and the Real World
**Score: 5/5 (Excellent)**
- **Positive:** The vertical flowchart naturally maps to the sequential execution of a test scenario.
- **Positive:** Icons (Globe for HTTP, Clock for Wait, Shield for Assert) are intuitive and standard.
- **Positive:** Terms like "Flow", "Step", and "Action" match user mental models.

### 3. User Control and Freedom
**Score: 3/5 (Needs Improvement)**
- **Positive:** Users can toggle the YAML editor panel visibility ("Show/Hide Editor").
- **Negative:** No "Reset" or "Undo" buttons. If a user pastes bad YAML over good YAML, they rely entirely on the browser's undo history.
- **Recommendation:** Add a "Reset to Sample" button and a "Clear" button.

### 4. Consistency and Standards
**Score: 5/5 (Excellent)**
- **Positive:** Strong color coding system (Cyan=HTTP, Amber=Wait, Emerald=Assert, Purple=Branch) is used consistently across nodes, legends, and detail panels.
- **Positive:** UI components (Glassmorphism) match the rest of the Turbulence dashboard.

### 5. Error Prevention
**Score: 4/5 (Good)**
- **Positive:** The parser (`yamlParser.ts`) catches syntax errors and displays friendly messages ("Line 5: Missing required field").
- **Positive:** The visualizer doesn't crash on invalid input; it just stops updating.
- **Recommendation:** Implement schema validation highlighting *before* parsing fails, perhaps via a smarter editor component.

### 6. Recognition Rather Than Recall
**Score: 4/5 (Good)**
- **Positive:** Nodes display critical info (Name, Type, Description) upfront.
- **Positive:** The "Step Detail Panel" allows deep inspection without context switching or remembering configuration.
- **Recommendation:** Add tooltips on node headers to show full service URLs without clicking.

### 7. Flexibility and Efficiency of Use
**Score: 3/5 (Acceptable)**
- **Positive:** "Upload YAML" button is a great accelerator.
- **Positive:** MiniMap and Zoom controls aid navigation in large flows.
- **Negative:** Lack of keyboard shortcuts (e.g., `Cmd+Enter` to force parse, `Cmd+S` to save local draft).

### 8. Aesthetic and Minimalist Design
**Score: 5/5 (Excellent)**
- **Positive:** High-contrast, dark mode interface reduces eye strain.
- **Positive:** Visual hierarchy is clear; the flow is the hero, the editor is the tool.
- **Critical Issue:** The YAML editor is a plain `<textarea>`. It lacks syntax highlighting, line numbers, and auto-indentation, which degrades the aesthetic and usability significantly.

### 9. Help Users Recognize, Diagnose, and Recover from Errors
**Score: 4/5 (Good)**
- **Positive:** Error messages are specific and located contextually near the input.
- **Recommendation:** Make the error message clickable to scroll the textarea to the offending line.

### 10. Help and Documentation
**Score: 2/5 (Weak)**
- **Negative:** No "Help" or "Docs" button explaining YAML syntax or supported fields.
- **Recommendation:** Add a "Syntax Guide" modal or link to documentation.

---

## Top 3 Actionable Improvements

1.  **Upgrade the Editor:** Replace the `<textarea>` with a proper code editor (Monaco or CodeMirror) to provide syntax highlighting and line numbers. This massively impacts Heuristics 5 (Error Prevention) and 8 (Aesthetics).
2.  **Visual Status Indicator:** Add a small "Saved/Parsing" indicator to satisfy Heuristic 1 (Visibility).
3.  **Keyboard Shortcuts:** Add support for common actions to improve Heuristic 7 (Efficiency).
