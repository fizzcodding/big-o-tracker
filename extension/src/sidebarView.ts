// import * as vscode from "vscode";
// import { runAnalyzer } from "./analyzerClient";

// export class BigOSidebarView implements vscode.WebviewViewProvider {
//   constructor(private readonly extensionUri: vscode.Uri) {}

//   resolveWebviewView(view: vscode.WebviewView) {
//     view.webview.options = { enableScripts: true };
//     view.webview.html = this.html();

//     view.webview.onDidReceiveMessage(async (msg) => {
//       if (msg.command !== "run") return;

//       const editor = vscode.window.activeTextEditor;
//       if (!editor || editor.document.languageId !== "python") {
//         view.webview.postMessage({
//           error: "Open a Python file first."
//         });
//         return;
//       }

//       const result = await runAnalyzer(editor.document.getText());
//       view.webview.postMessage({ result });
//     });
//   }

//   html(): string {
//     return `
//       <!DOCTYPE html>
//       <html>
//       <body>
//         <h3>Big-O Tracker</h3>

//         <label>Language</label>
//         <select disabled>
//           <option selected>Python (v0)</option>
//         </select>

//         <br/><br/>
//         <button onclick="run()">Run Analysis</button>

//         <pre id="output"></pre>

//         <script>
//           const vscode = acquireVsCodeApi();

//           function run() {
//             vscode.postMessage({ command: "run" });
//           }

//           window.addEventListener("message", e => {
//             const out = document.getElementById("output");
//             if (e.data.error) {
//               out.textContent = e.data.error;
//               return;
//             }

//             out.textContent = "";
//             e.data.result.forEach(fn => {
//               out.textContent += 
//                 fn.function + "\\n" +
//                 "  Time:  " + fn.time + "\\n" +
//                 "  Space: " + fn.space + "\\n\\n";
//             });
//           });
//         </script>
//       </body>
//       </html>
//     `;
//   }
// }
import * as vscode from "vscode";
import { analyzeSource } from "./analyzerClient";

export class BigOSidebarView implements vscode.WebviewViewProvider {
    public static readonly viewType = "bigOView";
    private _view?: vscode.WebviewView;

    resolveWebviewView(view: vscode.WebviewView, context: vscode.WebviewViewResolveContext, _token: vscode.CancellationToken) {
        this._view = view;

        view.webview.options = {
            enableScripts: true,
            localResourceRoots: []
        };

        // Set HTML immediately
        view.webview.html = this.getHtmlForWebview(view.webview);

        // Handle messages from webview
        view.webview.onDidReceiveMessage(async (msg) => {
            if (msg.command !== "analyze") return;

            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                view.webview.postMessage({ results: null, error: "❌ No active file" });
                return;
            }

            if (editor.document.languageId !== "python") {
                view.webview.postMessage({ results: null, error: "❌ Please open a Python file first" });
                return;
            }

            try {
                const source = editor.document.getText();
                const results = await analyzeSource(source);
                view.webview.postMessage({ results: results, error: null });
            } catch (e: any) {
                view.webview.postMessage({
                    results: null,
                    error: "❌ Error:\n" + e.toString()
                });
            }
        });
    }

    private getHtmlForWebview(webview: vscode.Webview): string {
        return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 0;
            margin: 0;
            background-color:transparent;
            color: #ffffff;
        }
        .header {
            padding: 10px;
            border-bottom: 1px solid #3e3e3e;
        }
        h3 {
            margin: 0 0 5px 0;
            font-size: 14px;
            font-weight: 600;
        }
        .subtitle {
            font-size: 11px;
            color: #cccccc;
            margin-bottom: 10px;
        }
        button {
            padding: 6px 14px;
            cursor: pointer;
            background: #0e639c;
            color: #ffffff;
            border: none;
            border-radius: 3px;
            font-size: 12px;
            font-family: var(--vscode-font-family);
        }
        button:hover {
            background: #1177bb;
        }
        button:active {
            background: #0a4d75;
        }
        #results {
            padding: 10px;
        }
        .function-card {
            background-color: #1e1e1e;
            border: 1px solid #3e3e3e;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 12px;
        }
        .function-name {
            text-align: center;
            font-size: 16px;
            font-weight: 600;
            color: #4fc3f7;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #3e3e3e;
        }
        .complexity-line {
            color: #ffffff;
            font-size: 13px;
            margin: 6px 0;
            line-height: 1.6;
        }
        .complexity-label {
            color: #cccccc;
        }
        .complexity-value {
            color: #ffffff;
            font-weight: 500;
        }
        .loops-recursion {
            color: #ffffff;
            font-size: 13px;
            margin-top: 6px;
        }
        .error {
            color: #f48771;
            padding: 10px;
            background-color: #3a2525;
            border: 1px solid #5a3a3a;
            border-radius: 4px;
            margin: 10px;
            white-space: pre-wrap;
        }
        .empty-state {
            color: #888888;
            text-align: center;
            padding: 20px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h3>Big-O Tracker</h3>
        <div class="subtitle">Analyze Python files for time and space complexity</div>
        <button id="btn">Run Analysis</button>
    </div>
    <div id="results"></div>

    <script>
        const vscode = acquireVsCodeApi();
        const btn = document.getElementById("btn");
        const resultsDiv = document.getElementById("results");

        btn.addEventListener("click", function() {
            resultsDiv.innerHTML = '<div class="empty-state">Analyzing...</div>';
            vscode.postMessage({ command: "analyze" });
        });

        function renderResults(results) {
            if (!results || results.length === 0) {
                resultsDiv.innerHTML = '<div class="empty-state">No functions found</div>';
                return;
            }

            resultsDiv.innerHTML = results.map(func => {
                return '<div class="function-card">' +
                    '<div class="function-name">' + func.function + '</div>' +
                    '<div class="complexity-line">' +
                    '<span class="complexity-label">Time complexity :</span> ' +
                    '<span class="complexity-value">' + func.big_o + '</span>' +
                    '</div>' +
                    '<div class="complexity-line">' +
                    '<span class="complexity-label">Space complexity :</span> ' +
                    '<span class="complexity-value">' + (func.space_complexity || 'O(1)') + '</span>' +
                    '</div>' +
                    '<div class="loops-recursion">' +
                    '<span class="complexity-label">Loops:</span> ' +
                    '<span class="complexity-value">' + func.loops + '</span> ' +
                    '<span class="complexity-label" style="margin-left: 15px;">Recursion:</span> ' +
                    '<span class="complexity-value">' + func.recursion + '</span>' +
                    '</div>' +
                    '</div>';
            }).join('');
        }

        window.addEventListener("message", function(event) {
            const message = event.data;
            if (message.error) {
                resultsDiv.innerHTML = '<div class="error">' + message.error + '</div>';
            } else if (message.results) {
                renderResults(message.results);
            }
        });
    </script>
</body>
</html>`;
    }
}