/**
 * ScenarioVisualizerPage
 *
 * Visual flowchart rendering of YAML scenarios with clickable steps.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import {
    ReactFlow,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    type Node,
    type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import Editor, { loader, type Monaco } from '@monaco-editor/react';
import {
    FileUp,
    Eye,
    EyeOff,
    RefreshCw,
    Trash2,
    RotateCcw,
    CheckCircle2,
    AlertCircle,
    Loader2,
    HelpCircle,
    Copy,
    Check
} from 'lucide-react';

import { parseScenario, type ScenarioStep } from '@/lib/yamlParser';
import { generateFlowElements } from '@/lib/flowUtils';
import { ScenarioNode, type ScenarioNodeData } from '@/components/flow/ScenarioNode';
import { FlowLegend } from '@/components/flow/FlowLegend';
import { StepDetailPanel } from '@/components/flow/StepDetailPanel';
import { Modal } from '@/components/Modal';
import { ScenarioSyntaxHelp } from '@/components/ScenarioSyntaxHelp';

// Configure monaco to use a cdn or local if preferred
loader.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.43.0/min/vs' } });

// localStorage key for autosave persistence
const STORAGE_KEY = 'turbulence_visualizer_yaml';

// Sample YAML for initial state
const SAMPLE_YAML = `# Sample Scenario
id: sample-flow
description: A simple API test flow

flow:
  - type: http
    name: get_users
    service: api
    method: GET
    path: /api/users
    extract:
      first_user_id: "$.data[0].id"

  - type: assert
    name: verify_success
    expect:
      status_code: 200

  - type: http
    name: get_user_details
    service: api
    method: GET
    path: "/api/users/{{first_user_id}}"
    extract:
      user_name: "$.name"

  - type: wait
    name: wait_for_processing
    service: api
    path: "/api/jobs/123"
    interval_seconds: 1
    timeout_seconds: 30
    expect:
      jsonpath: "$.status"
      equals: "complete"

  - type: assert
    name: final_check
    expect:
      jsonpath: "$.success"
      equals: "true"
`;

const nodeTypes = {
    scenario: ScenarioNode,
};

// Load initial YAML from localStorage or use sample
function getInitialYaml(): string {
    if (typeof window === 'undefined') return SAMPLE_YAML;
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved || SAMPLE_YAML;
}

export function ScenarioVisualizerPage() {
    const [yamlInput, setYamlInput] = useState(getInitialYaml);
    const [parseError, setParseError] = useState<string | null>(null);
    const [selectedStep, setSelectedStep] = useState<ScenarioStep | null>(null);
    const [showYamlPanel, setShowYamlPanel] = useState(true);
    const [isParsing, setIsParsing] = useState(false);
    const [lastParsed, setLastParsed] = useState<Date | null>(null);
    const [showHelp, setShowHelp] = useState(false);
    const [showClearConfirm, setShowClearConfirm] = useState(false);
    const [copied, setCopied] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const editorRef = useRef<any>(null);
    const monacoRef = useRef<Monaco | null>(null);

    const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

    // Parse YAML and generate flow
    const parseAndRender = useCallback((yaml: string) => {
        setIsParsing(true);
        // Artificial delay for feedback if it's too fast
        const start = Date.now();

        const result = parseScenario(yaml);

        const applyResult = () => {
            if (result.error) {
                const errorMsg = result.error.line
                    ? `Line ${result.error.line}: ${result.error.message}`
                    : result.error.message;
                setParseError(errorMsg);
            } else {
                setParseError(null);
                if (result.scenario) {
                    const { nodes: newNodes, edges: newEdges } = generateFlowElements(result.scenario);
                    setNodes(newNodes);
                    setEdges(newEdges);
                    setLastParsed(new Date());
                }
            }
            setIsParsing(false);
        };

        const elapsed = Date.now() - start;
        if (elapsed < 300) {
            setTimeout(applyResult, 300 - elapsed);
        } else {
            applyResult();
        }
    }, [setNodes, setEdges]);

    // Update Monaco markers when parse error changes
    useEffect(() => {
        if (!monacoRef.current || !editorRef.current) return;

        const model = editorRef.current.getModel();
        if (!model) return;

        if (parseError) {
            const lineMatch = parseError.match(/Line (\d+):/);
            const line = lineMatch ? parseInt(lineMatch[1], 10) : 1;
            const message = lineMatch ? parseError.replace(/Line \d+:\s*/, '') : parseError;

            monacoRef.current.editor.setModelMarkers(model, 'yaml-parser', [{
                startLineNumber: line,
                startColumn: 1,
                endLineNumber: line,
                endColumn: model.getLineMaxColumn(line),
                message,
                severity: monacoRef.current.MarkerSeverity.Error,
            }]);
        } else {
            monacoRef.current.editor.setModelMarkers(model, 'yaml-parser', []);
        }
    }, [parseError]);

    // Initial parse
    useEffect(() => {
        parseAndRender(yamlInput);
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // Handle YAML input changes with debounce
    const handleYamlChange = useCallback((value: string | undefined) => {
        const val = value || '';
        setYamlInput(val);
        // Debounce parsing
        const timer = setTimeout(() => {
            parseAndRender(val);
        }, 800);
        return () => clearTimeout(timer);
    }, [parseAndRender]);

    // Keyboard Shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Force parse
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                e.preventDefault();
                parseAndRender(yamlInput);
                return;
            }

            // Arrow key navigation between nodes
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                // Don't navigate if editor is focused
                const activeElement = document.activeElement;
                if (activeElement?.closest('.monaco-editor')) return;

                e.preventDefault();

                if (nodes.length === 0) return;

                const currentIndex = selectedStep
                    ? nodes.findIndex(n => (n.data as ScenarioNodeData).step.name === selectedStep.name)
                    : -1;

                let nextIndex: number;
                if (e.key === 'ArrowDown') {
                    nextIndex = currentIndex < nodes.length - 1 ? currentIndex + 1 : 0;
                } else {
                    nextIndex = currentIndex > 0 ? currentIndex - 1 : nodes.length - 1;
                }

                const nextNode = nodes[nextIndex];
                if (nextNode) {
                    setSelectedStep((nextNode.data as ScenarioNodeData).step);
                }
            }

            // Escape to deselect
            if (e.key === 'Escape' && selectedStep) {
                setSelectedStep(null);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [yamlInput, parseAndRender, nodes, selectedStep]);

    // Autosave to localStorage
    useEffect(() => {
        localStorage.setItem(STORAGE_KEY, yamlInput);
    }, [yamlInput]);

    // Handle file upload
    const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const content = event.target?.result as string;
            setYamlInput(content);
            parseAndRender(content);
        };
        reader.readAsText(file);
    }, [parseAndRender]);

    // Handle node click
    const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
        const data = node.data as ScenarioNodeData;
        if (data?.step) {
            setSelectedStep(data.step);
        }
    }, []);

    // Handle pane click (deselect)
    const handlePaneClick = useCallback(() => {
        setSelectedStep(null);
    }, []);

    const resetToSample = () => {
        setYamlInput(SAMPLE_YAML);
        parseAndRender(SAMPLE_YAML);
    };

    const clearEditor = () => {
        setYamlInput('');
        setNodes([]);
        setEdges([]);
        setParseError(null);
        setShowClearConfirm(false);
        localStorage.removeItem(STORAGE_KEY);
    };

    const goToErrorLine = () => {
        if (!parseError || !editorRef.current) return;
        const match = parseError.match(/Line (\d+):/);
        if (match) {
            const line = parseInt(match[1], 10);
            editorRef.current.revealLineInCenter(line);
            editorRef.current.setPosition({ lineNumber: line, column: 1 });
            editorRef.current.focus();
        }
    };

    const copyToClipboard = () => {
        navigator.clipboard.writeText(yamlInput);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="h-[calc(100vh-120px)] flex flex-col gap-6 animate-in fade-in duration-700">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold tracking-tight text-white glow-cyan mb-2">
                        Scenario Visualizer
                    </h1>
                    <div className="flex items-center gap-3">
                        <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">
                            YAML → Flowchart Rendering
                        </p>
                        {lastParsed && (
                            <span className="flex items-center gap-1.5 text-[10px] py-0.5 px-2 rounded-full bg-slate-800/50 text-slate-400 border border-white/5">
                                <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                                Last updated: {lastParsed.toLocaleTimeString()}
                            </span>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setShowYamlPanel(!showYamlPanel)}
                        className={`px-4 py-2 rounded-xl glass text-xs font-bold uppercase tracking-widest transition-all flex items-center gap-2 ${showYamlPanel ? 'text-cyan-400' : 'text-slate-500'
                            }`}
                    >
                        {showYamlPanel ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        {showYamlPanel ? 'Hide Editor' : 'Show Editor'}
                    </button>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".yaml,.yml"
                        onChange={handleFileUpload}
                        className="hidden"
                    />
                    <button
                        onClick={() => setShowHelp(true)}
                        className="px-4 py-2 rounded-xl glass glass-hover text-slate-400 hover:text-white text-xs font-bold uppercase tracking-widest flex items-center gap-2"
                    >
                        <HelpCircle className="w-4 h-4" />
                        Help
                    </button>
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="px-4 py-2 rounded-xl glass glass-hover text-cyan-400 text-xs font-bold uppercase tracking-widest flex items-center gap-2"
                    >
                        <FileUp className="w-4 h-4" />
                        Upload YAML
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex gap-4 min-h-0">
                {/* YAML Editor Panel */}
                {showYamlPanel && (
                    <div className="w-[450px] flex flex-col glass rounded-2xl overflow-hidden border border-white/5 shadow-2xl">
                        <div className="px-4 py-3 bg-slate-900/50 border-b border-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                                    YAML Input
                                </p>
                                {isParsing && (
                                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20">
                                        <Loader2 className="w-3 h-3 text-cyan-400 animate-spin" />
                                        <span className="text-[9px] font-bold text-cyan-400 uppercase tracking-tighter">Syncing</span>
                                    </div>
                                )}
                            </div>
                            <div className="flex items-center gap-1">
                                <button
                                    onClick={copyToClipboard}
                                    title="Copy YAML"
                                    className="p-1.5 rounded-lg hover:bg-white/5 text-slate-500 hover:text-cyan-400 transition-colors"
                                >
                                    {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                                </button>
                                <button
                                    onClick={resetToSample}
                                    title="Reset to sample"
                                    className="p-1.5 rounded-lg hover:bg-white/5 text-slate-500 hover:text-cyan-400 transition-colors"
                                >
                                    <RotateCcw className="w-3.5 h-3.5" />
                                </button>
                                <button
                                    onClick={() => parseAndRender(yamlInput)}
                                    title="Force parse (Cmd+Enter)"
                                    className="p-1.5 rounded-lg hover:bg-white/5 text-slate-500 hover:text-cyan-400 transition-colors"
                                >
                                    <RefreshCw className="w-3.5 h-3.5" />
                                </button>
                                <button
                                    onClick={() => setShowClearConfirm(true)}
                                    title="Clear all"
                                    className="p-1.5 rounded-lg hover:bg-white/5 text-slate-500 hover:text-rose-400 transition-colors"
                                >
                                    <Trash2 className="w-3.5 h-3.5" />
                                </button>
                            </div>
                        </div>
                        <div className="flex-1 min-h-0 bg-[#1e1e1e]">
                            <Editor
                                height="100%"
                                defaultLanguage="yaml"
                                value={yamlInput}
                                onChange={handleYamlChange}
                                theme="vs-dark"
                                onMount={(editor, monaco) => {
                                    editorRef.current = editor;
                                    monacoRef.current = monaco;
                                }}
                                options={{
                                    minimap: { enabled: false },
                                    fontSize: 13,
                                    lineNumbers: 'on',
                                    roundedSelection: true,
                                    scrollBeyondLastLine: false,
                                    readOnly: false,
                                    automaticLayout: true,
                                    padding: { top: 16, bottom: 16 },
                                    glyphMargin: false,
                                    folding: true,
                                    lineDecorationsWidth: 10,
                                    lineNumbersMinChars: 3,
                                    wordWrap: 'on',
                                    smoothScrolling: true,
                                    cursorBlinking: 'smooth',
                                    cursorSmoothCaretAnimation: 'on',
                                    bracketPairColorization: { enabled: true },
                                    renderLineHighlight: 'all',
                                }}
                            />
                        </div>
                        {parseError && (
                            <button
                                onClick={goToErrorLine}
                                className="px-4 py-3 bg-rose-500/10 border-t border-rose-500/20 flex items-start gap-3 text-left hover:bg-rose-500/20 transition-all group"
                            >
                                <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
                                <div className="flex-1">
                                    <p className="text-xs font-mono text-rose-400 leading-relaxed">{parseError}</p>
                                    <p className="text-[9px] font-bold text-rose-500/60 uppercase tracking-widest mt-1 group-hover:text-rose-400 transition-colors">
                                        Click to jump to line
                                    </p>
                                </div>
                            </button>
                        )}
                        <div className="px-4 py-2 border-t border-white/5 bg-slate-900/50 flex items-center justify-between">
                            <span className="text-[9px] text-slate-500 font-medium tracking-tight">CMD/CTRL + ENTER TO FORCE PARSE</span>
                            <span className="text-[9px] text-slate-600 font-bold uppercase">{yamlInput.length} chars</span>
                        </div>
                    </div>
                )}

                {/* Flow Canvas */}
                <div className="flex-1 glass rounded-2xl overflow-hidden relative border border-white/5 shadow-2xl">
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onNodeClick={handleNodeClick}
                        onPaneClick={handlePaneClick}
                        nodeTypes={nodeTypes}
                        fitView
                        fitViewOptions={{ padding: 0.2 }}
                        minZoom={0.3}
                        maxZoom={2}
                        proOptions={{ hideAttribution: true }}
                    >
                        <Background color="#334155" gap={20} size={1} />
                        <Controls
                            className="!bg-slate-900/80 !border-white/10 !rounded-lg !shadow-xl"
                            showInteractive={false}
                        />
                        <MiniMap
                            className="!bg-slate-900/80 !border-white/10 !rounded-lg"
                            nodeColor={(node) => {
                                const data = node.data as ScenarioNodeData | undefined;
                                const type = data?.step?.type;
                                switch (type) {
                                    case 'http': return '#06b6d4';
                                    case 'wait': return '#f59e0b';
                                    case 'assert': return '#10b981';
                                    case 'branch': return '#a855f7';
                                    default: return '#64748b';
                                }
                            }}
                            maskColor="rgba(0,0,0,0.7)"
                        />
                    </ReactFlow>
                    {/* Visual Indicators Overlay */}
                    {!isParsing && nodes.length > 0 && (
                        <div className="absolute top-4 right-20 pointer-events-none">
                            <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full animate-in slide-in-from-top-4 duration-500">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">{nodes.length} Actions Rendered</span>
                            </div>
                        </div>
                    )}
                    <FlowLegend />
                </div>

                {/* Step Detail Panel */}
                <StepDetailPanel
                    step={selectedStep}
                    onClose={() => setSelectedStep(null)}
                />
            </div>

            {/* Help Modal */}
            <Modal
                isOpen={showHelp}
                onClose={() => setShowHelp(false)}
                title="Scenario Syntax Guide"
                maxWidth="max-w-2xl"
            >
                <ScenarioSyntaxHelp />
            </Modal>

            {/* Clear Confirmation Modal */}
            <Modal
                isOpen={showClearConfirm}
                onClose={() => setShowClearConfirm(false)}
                title="Clear Editor"
                maxWidth="max-w-md"
            >
                <div className="space-y-4">
                    <p className="text-slate-300">
                        Are you sure you want to clear the editor? This will remove all your YAML content and cannot be undone.
                    </p>
                    <div className="flex justify-end gap-3">
                        <button
                            onClick={() => setShowClearConfirm(false)}
                            className="px-4 py-2 rounded-xl glass text-slate-400 hover:text-white text-sm font-medium transition-all"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={clearEditor}
                            className="px-4 py-2 rounded-xl bg-rose-500/20 border border-rose-500/30 text-rose-400 hover:bg-rose-500/30 text-sm font-medium transition-all"
                        >
                            Clear All
                        </button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}

export default ScenarioVisualizerPage;
