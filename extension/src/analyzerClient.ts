// import { spawn } from "child_process";
// import * as path from "path";

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
import { spawn } from "child_process";
import * as path from "path";

export function analyzeSource(sourceCode: string): Promise<any[]> {
  return new Promise((resolve, reject) => {
    /**
     * __dirname → extension/out
     * go up twice → big-o-tracker/
     */
    const projectRoot = path.resolve(__dirname, "..", "..");

    const proc = spawn(
      "python3",
      ["-m", "analyzer.main"],
      {
        cwd: projectRoot, // ✅ contains analyzer/
        env: {
          ...process.env,
          PYTHONPATH: projectRoot // ✅ makes imports bulletproof
        }
      }
    );

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
      } catch {
        reject("Invalid analyzer output:\n" + stdout);
      }
    });
  });
}
