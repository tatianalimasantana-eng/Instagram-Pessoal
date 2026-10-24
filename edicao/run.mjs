import { pipeline, env } from '@huggingface/transformers';
import fs from 'fs'; import path from 'path';
env.allowRemoteModels = false; env.localModelPath = process.argv[2];
const asr = await pipeline('automatic-speech-recognition', 'Xenova/whisper-small', { dtype: 'q8' });
const dir = process.argv[3]; const out = {};
const files = fs.readdirSync(dir).filter(f=>f.endsWith('.f32')).sort((a,b)=>a.slice(9).localeCompare(b.slice(9)));
for (const f of files) {
  const buf = fs.readFileSync(path.join(dir,f));
  const audio = new Float32Array(buf.buffer, buf.byteOffset, buf.length/4);
  let r;
  try { r = await asr(audio, { language:'portuguese', task:'transcribe', return_timestamps:'word', chunk_length_s:30 }); }
  catch(e) { console.error('word ts failed', e.message); r = await asr(audio, { language:'portuguese', task:'transcribe', return_timestamps:true, chunk_length_s:30 }); }
  out[f] = r.chunks.map(c=>[c.timestamp[0], c.timestamp[1], c.text]);
  console.log('==', f); console.log(r.chunks.map(c=>`${c.text}[${c.timestamp[0]?.toFixed(2)}]`).join(''));
}
fs.writeFileSync(process.argv[4], JSON.stringify(out));
