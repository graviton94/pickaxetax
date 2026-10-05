// Reads a JSON array of input texts on stdin, prints the browser engine's output.
import { analyzeInput } from "../../site/engine.js";

let data = "";
for await (const chunk of process.stdin) data += chunk;
const out = JSON.parse(data).map((text) => {
  try {
    return { ok: analyzeInput(text) };
  } catch (e) {
    return { error: e.message };
  }
});
process.stdout.write(JSON.stringify(out));
