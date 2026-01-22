/**
 * React Flow Utilities
 * 
 * Logic for converting scenarios into flowchart elements.
 */

import { type Node, type Edge } from '@xyflow/react';
import { getStepLabel, getStepDescription, type Scenario } from './yamlParser';
import { type ScenarioNodeData } from '@/components/flow/ScenarioNode';

/**
 * Generate React Flow nodes and edges for a scenario.
 */
export function generateFlowElements(scenario: Scenario): { nodes: Node[]; edges: Edge[] } {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    const nodeSpacingY = 100;
    const startY = 50;

    // Generate nodes for flow steps
    scenario.flow.forEach((step, index) => {
        const nodeId = `step-${index}`;

        const nodeData: ScenarioNodeData = {
            step,
            label: getStepLabel(step),
            description: getStepDescription(step),
            index,
        };

        nodes.push({
            id: nodeId,
            type: 'scenario',
            position: { x: 0, y: startY + index * nodeSpacingY },
            data: nodeData,
        });

        // Create edge to next node
        if (index > 0) {
            edges.push({
                id: `edge-${index - 1}-${index}`,
                source: `step-${index - 1}`,
                target: nodeId,
                type: 'smoothstep',
                style: { stroke: '#475569', strokeWidth: 2 },
                animated: false,
            });
        }
    });

    // Center nodes horizontally
    const maxWidth = 280;
    nodes.forEach((node) => {
        node.position.x = -maxWidth / 2;
    });

    return { nodes, edges };
}
