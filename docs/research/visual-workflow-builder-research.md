# Visual Workflow Builder Library Research

**Status:** Research Complete  
**Date:** January 2, 2026  
**Related Feature:** Marketing Automation Workflow Builder (AUTO-1 through AUTO-6)  
**Priority:** HIGH

## Executive Summary

For the Marketing Automation Workflow Builder feature (AUTO-1 through AUTO-6), we need a drag-and-drop visual workflow canvas library. This document evaluates options for implementing a visual workflow builder.

## Requirements

### Functional Requirements
1. **Drag-and-drop interface** - Users must be able to drag nodes/actions onto a canvas
2. **Node connections** - Visual connections between workflow steps with arrows/lines
3. **Node configuration** - Ability to configure each node (triggers, actions, conditions)
4. **Validation** - Real-time workflow validation (e.g., detecting disconnected nodes, invalid paths)
5. **Testing mode** - Ability to test workflows before activation
6. **Workflow types needed:**
   - Form submission triggers
   - Email action triggers (open, click, reply)
   - Site tracking triggers
   - Deal change triggers
   - Score threshold triggers
   - Date-based triggers
   - Send email action
   - Wait conditions (time delay, until date, until condition)
   - If/Else branching logic
   - Add/Remove tags and lists
   - Update contact fields
   - Create/Update deal
   - Create task
   - Webhook action

### Non-Functional Requirements
1. **Performance** - Handle workflows with 50+ nodes without lag
2. **Browser compatibility** - Support modern browsers (Chrome, Firefox, Safari, Edge)
3. **Mobile responsive** - At least view mode on mobile devices
4. **Accessibility** - Keyboard navigation and screen reader support
5. **Integration** - Must work with React/Vue/Django backend
6. **License** - Open source or commercially viable license

## Library Options

### Option 1: React Flow (Recommended)

**Website:** https://reactflow.dev/  
**License:** MIT  
**GitHub Stars:** 17k+  
**Latest Version:** 11.x

**Pros:**
- ✅ Modern, actively maintained React library
- ✅ Excellent performance with large graphs (uses virtualization)
- ✅ Beautiful default styling, highly customizable
- ✅ Built-in features: minimap, controls, background patterns
- ✅ Strong TypeScript support
- ✅ Good documentation and examples
- ✅ Supports custom nodes and edges
- ✅ Edge validation and connection rules
- ✅ Pro version available with additional features (not required for MVP)
- ✅ Used by major companies (Stripe, Gatsby, etc.)

**Cons:**
- ⚠️ React-only (but we're using React for frontend)
- ⚠️ Learning curve for custom node implementation

**Example Use Cases:**
- Workflow automation builders
- State machines
- Flowcharts and diagrams
- Data pipelines

**Estimated Integration Effort:** 8-12 hours for basic implementation, 20-24 hours for full feature set

**Code Example:**
```jsx
import ReactFlow, { 
  addEdge, 
  Background, 
  Controls,
  MiniMap 
} from 'reactflow';

const AutomationBuilder = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
    >
      <Background />
      <Controls />
      <MiniMap />
    </ReactFlow>
  );
};
```

### Option 2: JointJS

**Website:** https://www.jointjs.com/  
**License:** MPL 2.0 (open source) / Commercial  
**GitHub Stars:** 4k+

**Pros:**
- ✅ Framework agnostic (works with React, Vue, Angular, vanilla JS)
- ✅ Very feature-rich
- ✅ Good documentation
- ✅ Supports complex diagram types

**Cons:**
- ⚠️ Commercial license required for advanced features
- ⚠️ Steeper learning curve
- ⚠️ Heavier library (larger bundle size)
- ⚠️ Not as modern as React Flow

**Estimated Integration Effort:** 16-20 hours

### Option 3: jsPlumb

**Website:** https://jsplumbtoolkit.com/  
**License:** MIT / Commercial  
**GitHub Stars:** 7k+

**Pros:**
- ✅ Mature, stable library
- ✅ Framework agnostic
- ✅ Good documentation

**Cons:**
- ⚠️ Older API design, less modern
- ⚠️ Commercial license required for advanced features
- ⚠️ Not optimized for large graphs
- ⚠️ Community less active

**Estimated Integration Effort:** 20-24 hours

### Option 4: Draw.io / mxGraph (Deprecated)

**Status:** ⚠️ **NOT RECOMMENDED** - mxGraph is no longer maintained

### Option 5: Build Custom Solution

**Pros:**
- ✅ Full control over features and behavior
- ✅ No licensing concerns
- ✅ Optimized for exact use case

**Cons:**
- ❌ Significant development time (80-120 hours)
- ❌ Ongoing maintenance burden
- ❌ Reinventing the wheel
- ❌ Likely less polished than established libraries
- ❌ No community support

**Estimated Integration Effort:** 80-120 hours (NOT RECOMMENDED)

## Comparison Matrix

| Feature | React Flow | JointJS | jsPlumb | Custom |
|---------|-----------|---------|---------|--------|
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Documentation | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | N/A |
| Community Support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| TypeScript Support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Customization | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Modern Stack Fit | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| License Cost | FREE | $$ | $$ | FREE |
| Time to Implement | 8-12h | 16-20h | 20-24h | 80-120h |

## Recommendation

**Selected Solution: React Flow** ✅

### Justification

1. **Best fit for our React stack** - Seamless integration with our frontend
2. **Excellent performance** - Handles large workflows efficiently
3. **Modern and actively maintained** - Regular updates and bug fixes
4. **Strong community** - Large user base and extensive examples
5. **Great DX (Developer Experience)** - TypeScript support, clear API, good docs
6. **Free and open source (MIT)** - No licensing costs
7. **Fast implementation** - Can have MVP in 8-12 hours
8. **Used in production** - Proven track record with major companies

### Implementation Plan

#### Phase 1: Basic Setup (4-6 hours)
- Install React Flow and dependencies
- Create basic AutomationBuilder component
- Implement node palette (triggers, actions, conditions)
- Basic drag-and-drop functionality
- Save/load workflow functionality

#### Phase 2: Custom Nodes (4-6 hours)
- Create custom node components for each trigger/action type
- Implement node configuration panels
- Add validation logic for connections
- Style nodes to match platform design system

#### Phase 3: Advanced Features (4-6 hours)
- If/Else branching logic
- Wait conditions
- Node grouping/collapsing
- Workflow testing mode
- Undo/redo functionality
- Keyboard shortcuts

#### Phase 4: Backend Integration (4-6 hours)
- API endpoints for saving/loading workflows
- Execution engine integration
- Testing infrastructure
- Error handling and retry logic

**Total Estimated Effort: 16-24 hours** (within the 48-64 hour budget for AUTO-1 through AUTO-6)

### Dependencies

```json
{
  "dependencies": {
    "reactflow": "^11.10.0",
    "@reactflow/background": "^11.3.0",
    "@reactflow/controls": "^11.2.0",
    "@reactflow/minimap": "^11.5.0"
  }
}
```

### Code Structure

```
src/frontend/src/
├── components/
│   └── automation/
│       ├── AutomationBuilder.tsx        // Main workflow builder
│       ├── NodePalette.tsx             // Drag-and-drop node library
│       ├── nodes/
│       │   ├── TriggerNode.tsx        // Base trigger node
│       │   ├── ActionNode.tsx         // Base action node
│       │   ├── ConditionNode.tsx      // If/Else branching
│       │   └── WaitNode.tsx           // Wait conditions
│       ├── NodeConfigPanel.tsx         // Node configuration sidebar
│       └── WorkflowToolbar.tsx         // Test, save, validate controls
└── services/
    └── automation/
        └── workflowService.ts          // API integration
```

## Alternative Considerations

### If React Flow doesn't meet needs:
- **Fallback Option 1:** JointJS (if we need framework-agnostic solution)
- **Fallback Option 2:** Build custom with D3.js (if we need very specific visualization requirements)

## References

- React Flow Documentation: https://reactflow.dev/learn
- React Flow Examples: https://reactflow.dev/examples
- React Flow GitHub: https://github.com/wbkd/react-flow
- Marketing Automation Workflows (ActiveCampaign): https://help.activecampaign.com/hc/en-us/articles/221870267
- HubSpot Workflows: https://knowledge.hubspot.com/workflows/create-workflows

## Next Steps

1. ✅ **Research Complete** - React Flow selected
2. [ ] Create POC (Proof of Concept) with React Flow (4 hours)
3. [ ] Review POC with team and gather feedback
4. [ ] Proceed with Phase 1 implementation
5. [ ] Update TODO.md to mark research task as complete

---

**Research Completed By:** Development Team  
**Approved By:** [Pending Review]  
**Implementation Target:** Q1 2026
