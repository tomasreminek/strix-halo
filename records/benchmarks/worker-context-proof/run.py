import json,time,urllib.request,concurrent.futures,pathlib,subprocess,traceback
ROOT=pathlib.Path(__file__).parent

def call(port, messages, limit=800, **kwargs):
 model='halogen-qwen3.8-flash-next' if port==18081 else 'ornith-1.5-9b-abliterated-rocmfp4-strix-lean'
 payload=dict(model=model,messages=messages,max_tokens=limit,temperature=0,**kwargs)
 start=time.time()
 req=urllib.request.Request(f'http://127.0.0.1:{port}/v1/chat/completions',json.dumps(payload).encode(),{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=1800) as r:d=json.load(r)
 return dict(seconds=time.time()-start,response=d)

def probe(n, tag):
 # Distractors are real source-like modules, with relevant facts separated.
 chunks=['# repository contract: START_KEY=cedar_87; fix clamp so both bounds apply.\ndef clamp(value, low, high):\n    return min(low, max(value, high))\n']
 for i in range(n):
  chunks.append(f'# module inventory_{i}.py\ndef inventory_{i}(items):\n    return sum(item.get("quantity", 0) for item in items)\n')
  if i==n//2:chunks.append('# repository contract: MID_KEY=opal_42\n')
 chunks.append('# repository contract: END_KEY=birch_93\n')
 prompt='Inspect this repository. Return ONLY a JSON object with keys start, middle, end containing the exact contract keys, and code containing corrected Python clamp function. No markdown.\n'+''.join(chunks)
 result=call(18081,[{'role':'user','content':prompt}],enable_thinking=False)
 (ROOT/(tag+'.json')).write_text(json.dumps(result,indent=2))
 text=result['response']['choices'][0]['message']['content'].strip()
 if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0]
 data=json.loads(text)
 assert [data[k] for k in ['start','middle','end']]==['cedar_87','opal_42','birch_93'],data
 # Execute untrusted generated code in a networkless, read-only container.
 code=data['code']+'\nfor x,lo,hi,want in [(-2,0,10,0),(5,0,10,5),(12,0,10,10),(0,0,0,0),(-8,-5,-1,-5)]:\n assert clamp(x,lo,hi)==want\nprint("PASS")\n'
 test=subprocess.run(['docker','run','--rm','--network=none','--read-only','--memory=128m','--cpus=1','--pids-limit=32','-i','--entrypoint','python3','ghcr.io/peonist-ai/halogen-flash-server:0.11.0','-I','-'],input=code,text=True,capture_output=True,timeout=30)
 result['test']={'returncode':test.returncode,'stdout':test.stdout,'stderr':test.stderr}
 assert test.returncode==0,result['test']
 result['pass']=True
 (ROOT/(tag+'.json')).write_text(json.dumps(result,indent=2))
 return {'tag':tag,'seconds':result['seconds'],'usage':result['response'].get('usage'),'pass':True}

summary=[]
try:
 for n,tag in [(900,'medium'),(1500,'long'),(1500,'long-repeat')]:
  print('START',tag,flush=True)
  with concurrent.futures.ThreadPoolExecutor(2) as ex:
   worker=ex.submit(probe,n,tag)
   main=ex.submit(call,18083,[{'role':'user','content':'Write a short Python function to validate balanced parentheses and three assertions.'}],256)
   m=main.result();(ROOT/(tag+'-ornith.json')).write_text(json.dumps(m,indent=2))
   summary.append(worker.result())
  print(json.dumps(summary[-1]),flush=True)
except Exception:
 summary.append({'error':traceback.format_exc()});print(traceback.format_exc(),flush=True)
finally:
 (ROOT/'summary.json').write_text(json.dumps(summary,indent=2))
 print('COMPLETE',json.dumps(summary),flush=True)
