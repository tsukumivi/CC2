"""Compile an unwrapped Main.java and run the capstone without the HTTP app.

Uses real JDK executables, a scratch working directory and fresh JVMs.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend import main
from backend.runner import normalized


def verify():
    tools=main.java_toolchain()
    assert tools['jdk_available'],tools
    capstone=next(c for c in main.get_course()['concepts'] if c['id']=='capstone-records')
    code=next(t['reference_code'] for t in capstone['tasks'] if t['kind']=='build')
    results=[]
    with tempfile.TemporaryDirectory(prefix='java-export-',dir=os.environ.get('TMPDIR',str(ROOT/'artifacts'))) as name:
        folder=Path(name)
        (folder/'Main.java').write_text(code,encoding='utf-8')
        compiled=main.run_bounded([tools['javac_path'],'-J-Xmx256m','-J-XX:+UseSerialGC','--release','21','-encoding','UTF-8','-proc:none','Main.java'],folder,'',20)
        assert compiled['exit_code']==0 and not compiled['timed_out'],compiled
        command=[tools['java_path'],'-Xmx128m','-XX:+UseSerialGC','-Dfile.encoding=UTF-8','-cp','.','Main']
        for label,stdin,expected in [('save','add|Orbit|2\nsave\nq\n','Added\nSaved\nBye\n'),('restart','list\nq\n','Orbit|2\nBye\n')]:
            actual=main.run_bounded(command,folder,stdin,4)
            good=actual['exit_code']==0 and not actual['timed_out'] and normalized(actual['stdout'])==normalized(expected)
            results.append({'case':label,'passed':good,'actual':actual,'expected_stdout':expected})
        data=(folder/'records.txt').read_text(encoding='utf-8')
        results.append({'case':'native saved file','passed':data=='Orbit|2\n','actual':data})
        (folder/'records.txt').write_text('Orbit|bad\n',encoding='utf-8')
        actual=main.run_bounded(command,folder,'q\n',4)
        data=(folder/'records.txt').read_text(encoding='utf-8')
        results.append({'case':'corrupt file is retained','passed':actual['exit_code']==0 and normalized(actual['stdout'])=='Load failed' and data=='Orbit|bad\n','actual':actual,'file_after_run':data})
    report={'passed':all(r['passed'] for r in results),'compiler':tools['compiler_version'],'no_http_server_required':True,'compiled_filename':'Main.java','results':results}
    (ROOT/'artifacts/portability-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    assert report['passed'],'Native export verification failed.'


if __name__=='__main__':
    verify()
