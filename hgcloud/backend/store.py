import hashlib,hmac,json,os,re,sqlite3,time,uuid
from pathlib import Path
ID=re.compile(r'^[0-9a-f]{32}$')
class Store:
    def __init__(self,root):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True,mode=0o700);self.root.chmod(0o700)
        self.db=self.root/'jobs.sqlite3'
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, owner TEXT NOT NULL, state TEXT NOT NULL, created REAL NOT NULL, payload TEXT NOT NULL, error TEXT)')
        self.db.chmod(0o600)
    def connect(self):
        c=sqlite3.connect(self.db,timeout=20);c.row_factory=sqlite3.Row;return c
    def folder(self,jid):
        if not ID.fullmatch(jid):raise KeyError(jid)
        p=self.root/jid
        if p.is_symlink():raise ValueError('Unsafe job path')
        return p
    def get(self,jid,owner=None):
        if not ID.fullmatch(jid):raise KeyError(jid)
        with self.connect() as c:r=c.execute('SELECT * FROM jobs WHERE id=?'+(' AND owner=?' if owner is not None else ''),(jid,owner) if owner is not None else (jid,)).fetchone()
        if not r:raise KeyError(jid)
        return dict(r)|{'payload':json.loads(r['payload'])}
    def create(self,owner,payload):
        jid=uuid.uuid4().hex
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            active=c.execute("SELECT count(*) FROM jobs WHERE owner=? AND state NOT IN ('FAILED','NEEDS_REVIEW','INTERRUPTED')",(owner,)).fetchone()[0]
            if active>=20:raise OverflowError('Active job limit reached')
            self.folder(jid).mkdir(mode=0o700)
            c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,NULL)',(jid,owner,'RECEIVING',time.time(),json.dumps(payload)))
        return jid
    def transition(self,jid,state,error=None):
        with self.connect() as c:c.execute('UPDATE jobs SET state=?,error=? WHERE id=?',(state,error,jid))
    def claim(self):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE');r=c.execute("SELECT id FROM jobs WHERE state='QUEUED' ORDER BY created LIMIT 1").fetchone()
            if r:c.execute("UPDATE jobs SET state='RUNNING',error=NULL WHERE id=?",(r['id'],))
        return self.get(r['id']) if r else None
