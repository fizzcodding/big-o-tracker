import * as vscode from "vscode";
import { BigOSidebarView } from "./sidebarView";

export function activate(context: vscode.ExtensionContext) {
  console.log("Big-O Tracker extension is activating...");
  
  try {
    const provider = new BigOSidebarView();
    
    const disposable = vscode.window.registerWebviewViewProvider(
      "bigOView", // Use string literal to ensure it matches package.json
      provider,
      {
        webviewOptions: {
          retainContextWhenHidden: true
        }
      }
    );
    
    context.subscriptions.push(disposable);
    console.log("Big-O Tracker webview provider registered successfully");
  } catch (error) {
    console.error("Error activating Big-O Tracker:", error);
    vscode.window.showErrorMessage(`Big-O Tracker activation failed: ${error}`);
  }
}

export function deactivate() {}