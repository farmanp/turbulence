import { Code, Settings, AlertCircle, Zap } from 'lucide-react';

export function ScenarioSyntaxHelp() {
    return (
        <div className="space-y-8 pb-4">
            <section>
                <div className="flex items-center gap-2 mb-4">
                    <Settings className="w-5 h-5 text-cyan-400" />
                    <h3 className="text-lg font-bold text-white">Metadata</h3>
                </div>
                <p className="text-slate-400 text-sm mb-4">
                    Every scenario starts with basic identification metadata.
                </p>
                <pre className="bg-slate-900/50 p-4 rounded-xl border border-white/5 text-xs font-mono text-cyan-200">
                    {`id: user-onboarding-test
description: Verifies fundamental user registration flow
variables:
  base_url: "https://api.example.com"
  default_timeout: 5`}
                </pre>
            </section>

            <section>
                <div className="flex items-center gap-2 mb-4">
                    <Code className="w-5 h-5 text-purple-400" />
                    <h3 className="text-lg font-bold text-white">Action Types</h3>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    <div className="glass p-4 rounded-2xl border border-white/5">
                        <h4 className="text-xs font-black uppercase text-cyan-500 mb-2">HTTP Action</h4>
                        <pre className="text-xs font-mono text-slate-300">
                            {`- type: http
  name: create_user
  service: main_api
  method: POST
  path: /users
  body:
    name: "John Doe"
  extract:
    user_id: "$.id"`}
                        </pre>
                    </div>

                    <div className="glass p-4 rounded-2xl border border-white/5">
                        <h4 className="text-xs font-black uppercase text-amber-500 mb-2">Wait Action</h4>
                        <pre className="text-xs font-mono text-slate-300">
                            {`- type: wait
  name: job_completion
  service: worker
  path: /jobs/{{job_id}}
  interval_seconds: 2
  timeout_seconds: 60
  expect:
    jsonpath: "$.status"
    equals: "finished"`}
                        </pre>
                    </div>

                    <div className="glass p-4 rounded-2xl border border-white/5">
                        <h4 className="text-xs font-black uppercase text-emerald-500 mb-2">Assert Action</h4>
                        <pre className="text-xs font-mono text-slate-300">
                            {`- type: assert
  name: validate_results
  expect:
    jsonpath: "$.items.length"
    greater_than: 0`}
                        </pre>
                    </div>

                    <div className="glass p-4 rounded-2xl border border-white/5">
                        <h4 className="text-xs font-black uppercase text-purple-500 mb-2">Branch Action</h4>
                        <pre className="text-xs font-mono text-slate-300">
                            {`- type: branch
  name: check_env
  condition: env == 'prod'
  if_true:
    - type: wait
      duration: 10
  if_false:
    - type: wait
      duration: 1`}
                        </pre>
                    </div>
                </div>
            </section>

            <section>
                <div className="flex items-center gap-2 mb-4">
                    <Zap className="w-5 h-5 text-amber-400" />
                    <h3 className="text-lg font-bold text-white">Templating</h3>
                </div>
                <p className="text-slate-400 text-sm mb-2">
                    Use <code className="text-cyan-400 font-mono">{"{{variable_name}}"}</code> to inject dynamic values from the context.
                </p>
                <div className="bg-slate-900/50 p-4 rounded-xl border border-white/5">
                    <p className="text-xs font-mono text-slate-300">path: /users/{"{{last_user_id}}"}/profile</p>
                </div>
            </section>

            <section>
                <div className="flex items-center gap-2 mb-4">
                    <AlertCircle className="w-5 h-5 text-rose-400" />
                    <h3 className="text-lg font-bold text-white">Validation Rules</h3>
                </div>
                <ul className="space-y-2 text-sm text-slate-400 list-disc ml-5">
                    <li>The <code className="text-slate-200">flow</code> field must be a list of actions.</li>
                    <li>Each action must have a <code className="text-slate-200">type</code> and <code className="text-slate-200">name</code>.</li>
                    <li>Conditions use Python-like syntax: <code className="text-slate-200">status == 200 and count &gt; 0</code>.</li>
                </ul>
            </section>
        </div>
    );
}
