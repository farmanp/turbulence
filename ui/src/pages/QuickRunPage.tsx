/**
 * QuickRunPage
 * 
 * Launcher interface for starting simulation runs from the UI.
 */

import { useState, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
    ReactFlow,
    Background,
    useNodesState,
    useEdgesState,
    type Node,
    type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { parseScenario } from '@/lib/yamlParser';
import { generateFlowElements } from '@/lib/flowUtils';
import { ScenarioNode } from '@/components/flow/ScenarioNode';
import { FlowLegend } from '@/components/flow/FlowLegend';

const nodeTypes = {
    scenario: ScenarioNode,
};

interface SUTConfig {
    name: string;
    path: string;
}

interface ScenarioMeta {
    name: string;
    id: string;
    path: string;
}

export function QuickRunPage() {
    const navigate = useNavigate();
    
    // Form state
    const [selectedSut, setSelectedSut] = useState('');
    const [selectedScenarioId, setSelectedScenarioId] = useState('');
    const [instances, setInstances] = useState(10);
    const [parallelism, setParallelism] = useState(5);
    const [profile, setProfile] = useState('');

    // Flow state for preview
    const [nodes, setNodes] = useNodesState<Node>([]);
    const [edges, setEdges] = useEdgesState<Edge>([]);

    // Fetch SUT configs
    const { data: sutData } = useQuery<{ configs: SUTConfig[] }>({
        queryKey: ['configs', 'sut'],
        queryFn: async () => {
            const res = await fetch('/api/configs/sut');
            if (!res.ok) throw new Error('Failed to fetch SUT configs');
            return res.json();
        }
    });

    // Fetch Scenarios
    const { data: scenarioData } = useQuery<{ scenarios: ScenarioMeta[] }>({
        queryKey: ['configs', 'scenarios'],
        queryFn: async () => {
            const res = await fetch('/api/configs/scenarios');
            if (!res.ok) throw new Error('Failed to fetch scenarios');
            return res.json();
        }
    });

    // Fetch Scenario Content for preview
    const { data: activeScenarioContent, isFetching: contentLoading } = useQuery<{ id: string, content: string }>({
        queryKey: ['configs', 'scenarios', selectedScenarioId],
        queryFn: async () => {
            if (!selectedScenarioId) return null;
            const res = await fetch(`/api/configs/scenarios/${selectedScenarioId}`);
            if (!res.ok) throw new Error('Failed to fetch scenario content');
            return res.json();
        },
        enabled: !!selectedScenarioId,
    });

    // Update preview when scenario content changes
    useMemo(() => {
        if (activeScenarioContent?.content) {
            const result = parseScenario(activeScenarioContent.content);
            if (result.scenario) {
                const { nodes: newNodes, edges: newEdges } = generateFlowElements(result.scenario);
                setNodes(newNodes);
                setEdges(newEdges);
            }
        } else {
            setNodes([]);
            setEdges([]);
        }
    }, [activeScenarioContent, setNodes, setEdges]);

    // Run Mutation
    const runMutation = useMutation({
        mutationFn: async () => {
            const res = await fetch('/api/runs/trigger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sut_path: selectedSut,
                    scenario_ids: [selectedScenarioId],
                    instances,
                    parallelism,
                    profile: profile || null,
                }),
            });
            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || 'Failed to trigger run');
            }
            return res.json();
        },
        onSuccess: (data) => {
            // Navigate to the new run detail page
            navigate(`/runs/${data.run_id}`);
        }
    });

    const isReady = !!selectedSut && !!selectedScenarioId;

    return (
        <div className="h-[calc(100vh-120px)] flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold tracking-tight text-white glow-cyan mb-2">
                    Quick Launch
                </h1>
                <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">
                    Manual execution configuration
                </p>
            </div>

            <div className="flex-1 flex gap-6 min-h-0">
                {/* Left: Configuration Form */}
                <div className="w-96 flex flex-col gap-6 overflow-auto pr-2">
                    {/* Selectors */}
                    <div className="glass rounded-2xl p-6 space-y-6">
                        <div className="space-y-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                                System Under Test
                            </label>
                            <select
                                value={selectedSut}
                                onChange={(e) => setSelectedSut(e.target.value)}
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:ring-2 ring-cyan-500/50 appearance-none cursor-pointer hover:bg-white/[0.08] transition-all"
                            >
                                <option value="" disabled>Select SUT configuration...</option>
                                {sutData?.configs.map(cfg => (
                                    <option key={cfg.path} value={cfg.path}>{cfg.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                                Workflow Scenario
                            </label>
                            <select
                                value={selectedScenarioId}
                                onChange={(e) => setSelectedScenarioId(e.target.value)}
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:ring-2 ring-cyan-500/50 appearance-none cursor-pointer hover:bg-white/[0.08] transition-all"
                            >
                                <option value="" disabled>Select scenario...</option>
                                {scenarioData?.scenarios.map(sc => (
                                    <option key={sc.id} value={sc.id}>{sc.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                                Environment Profile (Optional)
                            </label>
                            <input
                                type="text"
                                value={profile}
                                onChange={(e) => setProfile(e.target.value)}
                                placeholder="e.g. staging, prod"
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:ring-2 ring-cyan-500/50 hover:bg-white/[0.08] transition-all"
                            />
                        </div>
                    </div>

                    {/* Parameters */}
                    <div className="glass rounded-2xl p-6 space-y-8">
                        <div className="space-y-4">
                            <div className="flex justify-between items-end">
                                <label className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                                    Agent Population
                                </label>
                                <span className="text-xl font-bold text-cyan-400 tabular-nums">
                                    {instances}
                                </span>
                            </div>
                            <input
                                type="range"
                                min="1"
                                max="500"
                                step="1"
                                value={instances}
                                onChange={(e) => setInstances(parseInt(e.target.value))}
                                className="w-full h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                            />
                            <div className="flex justify-between text-[10px] font-bold text-slate-600">
                                <span>1</span>
                                <span>250</span>
                                <span>500</span>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="flex justify-between items-end">
                                <label className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                                    Concurrency Limit
                                </label>
                                <span className="text-xl font-bold text-indigo-400 tabular-nums">
                                    {parallelism}
                                </span>
                            </div>
                            <input
                                type="range"
                                min="1"
                                max="100"
                                step="1"
                                value={parallelism}
                                onChange={(e) => setParallelism(parseInt(e.target.value))}
                                className="w-full h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                            />
                            <div className="flex justify-between text-[10px] font-bold text-slate-600">
                                <span>1</span>
                                <span>50</span>
                                <span>100</span>
                            </div>
                        </div>
                    </div>

                    {/* Run Button */}
                    <button
                        disabled={!isReady || runMutation.isPending}
                        onClick={() => runMutation.mutate()}
                        className={`
                            w-full py-4 rounded-2xl font-black uppercase tracking-[0.2em] text-sm
                            transition-all duration-500 relative overflow-hidden group
                            ${isReady && !runMutation.isPending
                                ? 'bg-cyan-500 text-black shadow-[0_0_30px_rgba(6,182,212,0.4)] hover:scale-[1.02] active:scale-[0.98]'
                                : 'bg-white/5 text-slate-600 cursor-not-allowed'
                            }
                        `}
                    >
                        {runMutation.isPending ? (
                            <span className="flex items-center justify-center gap-2">
                                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                Deploying...
                            </span>
                        ) : (
                            'Initialize Simulation'
                        )}
                        
                        {/* Hover glow effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite] pointer-events-none" />
                    </button>
                    
                    {runMutation.isError && (
                        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20">
                            <p className="text-xs font-bold text-rose-400">
                                Launch Error: {runMutation.error instanceof Error ? runMutation.error.message : 'Unknown failure'}
                            </p>
                        </div>
                    )}
                </div>

                {/* Right: Scenario Preview */}
                <div className="flex-1 glass rounded-3xl overflow-hidden relative group">
                    <div className="absolute top-6 left-6 z-10 flex items-center gap-3">
                        <div className="px-3 py-1 rounded-md bg-black/40 backdrop-blur-md border border-white/10">
                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">
                                Scenario Preview
                            </p>
                        </div>
                        {contentLoading && (
                            <div className="w-4 h-4 rounded-full border-2 border-cyan-500/20 border-t-cyan-500 animate-spin" />
                        )}
                    </div>

                    {!selectedScenarioId ? (
                        <div className="h-full flex flex-col items-center justify-center text-center p-12">
                            <div className="w-20 h-20 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center mb-6">
                                <svg className="w-10 h-10 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                                </svg>
                            </div>
                            <h3 className="text-lg font-bold text-slate-400 mb-2">No Scenario Selected</h3>
                            <p className="text-sm text-slate-600 max-w-xs">
                                Select a workflow path from the dropdown to visualize the execution graph before deployment.
                            </p>
                        </div>
                    ) : (
                        <ReactFlow
                            nodes={nodes}
                            edges={edges}
                            nodeTypes={nodeTypes}
                            fitView
                            fitViewOptions={{ padding: 0.2 }}
                            minZoom={0.2}
                            maxZoom={1.5}
                            proOptions={{ hideAttribution: true }}
                            // Disable interactivity for simple preview
                            nodesDraggable={false}
                            nodesConnectable={false}
                            elementsSelectable={false}
                            zoomOnScroll={true}
                            zoomOnPinch={true}
                            panOnDrag={true}
                        >
                            <Background color="#334155" gap={20} size={1} />
                            <FlowLegend />
                        </ReactFlow>
                    )}
                </div>
            </div>
        </div>
    );
}
