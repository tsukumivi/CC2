from backend import main


def test_java_jobs_use_explicit_heap_budgets(client,monkeypatch):
    commands=[]
    original=main.run_bounded
    def observed(command,*args,**kwargs):
        commands.append(command)
        return original(command,*args,**kwargs)
    monkeypatch.setattr(main,'run_bounded',observed)
    r=client.post('/api/run',json={'source':'public class Main {public static void main(String[] a){System.out.println("budget");}}'}).json()
    assert r['status']=='completed',r
    assert '-J-Xmx256m' in commands[0]
    assert '-J-XX:+UseSerialGC' in commands[0]
    assert '-Xmx128m' in commands[1]
    assert '-XX:+UseSerialGC' in commands[1]


def test_a_missing_jdk_is_not_cached_forever(tmp_path,monkeypatch):
    root=main.ROOT_DIR
    main.java_toolchain.cache_clear()
    monkeypatch.delenv('JAVA_HOME',raising=False)
    monkeypatch.setattr(main.shutil,'which',lambda _:None)
    monkeypatch.setattr(main,'ROOT_DIR',tmp_path)
    assert main.java_toolchain()['jdk_available'] is False
    monkeypatch.setattr(main,'ROOT_DIR',root)
    assert main.java_toolchain()['jdk_available'] is True
