// stdin: JSON array of payloads -> stdout: JSON array of booleans (valid?)
import { validateContribution } from "../../site/contrib.js";

let data = "";
for await (const c of process.stdin) data += c;
process.stdout.write(JSON.stringify(JSON.parse(data).map((p) => validateContribution(p).length === 0)));
