"use strict";
// import { spawn } from "child_process";
// import * as path from "path";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.analyzeSource = analyzeSource;
// export function analyzeSource(sourceCode: string): Promise<string> {
//   return new Promise((resolve, reject) => {
//     const analyzerDir = path.join(
//       __dirname,
//       "..",
//       "..",
//       "..",
//       "analyzer"
//     );
//     // run: python -m analyzer.main
//     const proc = spawn("python3", ["-m", "analyzer.main"], {
//       cwd: path.join(analyzerDir, "..")
//     });
//     let stdout = "";
//     let stderr = "";
//     proc.stdout.on("data", d => (stdout += d.toString()));
//     proc.stderr.on("data", d => (stderr += d.toString()));
//     proc.stdin.write(sourceCode);
//     proc.stdin.end();
//     proc.on("close", () => {
//       if (stderr) {
//         reject(stderr);
//         return;
//       }
//       try {
//         const parsed = JSON.parse(stdout);
//         resolve(formatOutput(parsed));
//       } catch (e) {
//         reject("Invalid analyzer output:\n" + stdout);
//       }
//     });
//   });
// }
// function formatOutput(results: any[]): string {
//   if (!results.length) return "No functions found";
//   return results
//     .map(r =>
//       `Function: ${r.function}
//   Time Complexity:  ${r.big_o}
//   Space Complexity: ${r.space_complexity || "O(1)"}
//   Loops: ${r.loops}
//   Recursion: ${r.recursion}`
//     )
//     .join("\n\n");
// }
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
function analyzeSource(sourceCode) {
    return new Promise((resolve, reject) => {
        const extensionDir = path.resolve(__dirname, "..");
        const proc = (0, child_process_1.spawn)("python3", ["-m", "analyzer.main"], {
            cwd: extensionDir,
            env: {
                ...process.env,
                PYTHONPATH: extensionDir
            }
        });
        let stdout = "";
        let stderr = "";
        proc.stdout.on("data", d => (stdout += d.toString()));
        proc.stderr.on("data", d => (stderr += d.toString()));
        proc.stdin.write(sourceCode);
        proc.stdin.end();
        proc.on("close", () => {
            if (stderr) {
                reject(stderr);
                return;
            }
            try {
                const parsed = JSON.parse(stdout);
                resolve(parsed); // Return raw JSON, let the view format it
            }
            catch {
                reject("Invalid analyzer output:\n" + stdout);
            }
        });
    });
}
