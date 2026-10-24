import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { test } from 'node:test';
import assert from 'node:assert/strict';

const source = readFileSync(new URL('../../../config/coucou/open-session.js', import.meta.url), 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));

function fixture(reply = async () => ({ ok: true }), connected = true, immutable = false, selectedAgent = 'codex') {
  const requests = [], native = [], nodes = [];
  let hook;
  class Element {
    constructor(tag) { this.tag = tag; this.children = []; this.style = {}; this.value = ''; this.isConnected = true; nodes.push(this); }
    append(node) { this.children.push(node); }
    setAttribute() {}
    addEventListener(name, callback) { (this.events ||= {})[name] = callback; }
    replaceChildren() { this.children = []; }
    showModal() { this.open = true; }
    close() { this.open = false; }
    remove() { this.isConnected = false; }
    getBoundingClientRect() { return { x: 40, y: 0, width: 640, height: 300 }; }
  }
  const ipc = {
    transformCallback: callback => callback,
    invoke: async (command, args) => {
      native.push([command, args]);
      if (command === 'plugin:event|listen') hook = args.handler;
      return true;
    },
  };
  const window = { localStorage:{getItem:()=>selectedAgent}, __TAURI_INTERNALS__: ipc, webkit: { messageHandlers: {
    coucouAgentHub: { postMessage: async request => { requests.push(request); return reply(request); } },
  } } };
  if (immutable) {
    window.__coucouNativeInvoke = ipc.invoke;
    Object.defineProperty(ipc, 'invoke', { writable: false, value: function(cmd,args,options) {
      return window.__coucouAgentHubInvoke ? window.__coucouAgentHubInvoke(cmd,args,options) : window.__coucouNativeInvoke(cmd,args,options);
    } });
  }
  if (!connected) delete window.webkit.messageHandlers.coucouAgentHub;
  runInNewContext(source, { window, document: { createElement: tag => new Element(tag), body: new Element('body') },
    setInterval, clearInterval, console });
  return { ipc, requests, native, nodes,
    emit: payload => hook({ payload }) };
}

test('uses the selected native session and its actual adapter, never the last event', async () => {
  const f = fixture();
  f.emit({ coucou_agent: 'codex', session_id: 'codex-A', hook_event_name: 'Stop' });
  f.emit({ coucou_agent: 'codex', session_id: 'codex-B', hook_event_name: 'Stop' });
  f.emit({ coucou_agent: 'hermes', session_id: 'hermes-A', hook_event_name: 'Stop' });
  await f.ipc.invoke('open_session', { sessionId: 'codex-A', path: '/same/folder' });
  const request = f.requests.find(r => r.action === 'open');
  assert.equal(request.agent, 'codex');
  assert.equal(request.sessionId, 'codex-A');
  assert.equal(f.requests.filter(r => r.action === 'observe').length, 3);
  await f.ipc.invoke('open_session', { sessionId: 'hermes-A', path: '/same/folder' });
  assert.equal(f.requests.filter(r => r.action === 'open').at(-1).agent, 'hermes');
});

test('preserves supplied route IDs and deduplicates a double click', async () => {
  let release;
  const f = fixture(async request => request.action === 'open' ? await new Promise(resolve => { release = resolve; }) : { ok: true });
  const route = { version: 1, agente: 'hermes', idCarpeta: 'opaque ñ', idMessage: 'handoff-a";$(x)' };
  const first = f.ipc.invoke('open_session', { sessionId: 'native', agent: 'hermes', route });
  const second = f.ipc.invoke('open_session', { sessionId: 'native', agent: 'hermes', route });
  assert.equal(first, second);
  assert.equal(f.requests.length, 1);
  assert.equal(f.requests[0].route, route);
  release({ ok: true });
  assert.equal(await first, true);
});

test('legacy association dialog cancellation never creates or launches a conversation', async () => {
  const f = fixture(async request => request.action === 'open' ? { needsAssociation: true } : {
    ok: true, items: [{ id: 'codex', name: 'Codex', installed: true }, { id: 'hermes', name: 'Hermes', installed: true }] });
  const operation = f.ipc.invoke('open_session', { sessionId: null, path: '/old/task' });
  await flush();
  const dialog = f.nodes.find(n => n.tag === 'dialog');
  assert.ok(dialog.open);
  const cancel = f.nodes.find(n => n.textContent === 'Cancelar');
  cancel.onclick();
  assert.equal(await operation, false);
  assert.deepEqual(f.requests.map(r => r.action), ['open', 'agents']);
  assert.equal(dialog.isConnected, false);
});

test('ambiguity across adapters prompts selection; it does not pick Codex', async () => {
  const f = fixture(async request => request.action === 'open' ? { needsAssociation: true } : { ok: true, items: [] });
  for (const agent of ['codex', 'hermes']) f.emit({ coucou_agent: agent, session_id: 'shared-id', hook_event_name: 'Stop' });
  await flush();
  const operation = f.ipc.invoke('open_session', { sessionId: 'shared-id' });
  await flush();
  assert.equal(f.requests.find(r => r.action === 'open').agent, null);
  f.nodes.find(n => n.textContent === 'Cancelar').onclick();
  assert.equal(await operation, false);
});

test('hub errors are visible and never fall back to native open_session', async () => {
  const f = fixture(async () => ({ ok: false, error: 'La conversación fue eliminada' }));
  assert.equal(await f.ipc.invoke('open_session', { agent: 'hermes', sessionId: 'gone' }), false);
  assert.ok(f.nodes.find(n => n.textContent === 'La conversación fue eliminada'));
  assert.equal(f.native.filter(([command]) => command === 'open_session').length, 0);
  await f.ipc.invoke('unrelated_command', { unchanged: true });
  assert.equal(f.native.at(-1)[0], 'unrelated_command');
});

test('terminal dialogs keep the existing native window/input region available', async () => {
  const f = fixture(async () => ({ ok: false, error: 'Sesión bloqueada' }));
  await f.ipc.invoke('open_session', { sessionId: 'locked' });
  await f.ipc.invoke('set_collapsed', { collapsed: true });
  assert.equal(f.native.at(-1)[1].collapsed, false);
  await f.ipc.invoke('set_island_rect', { x: 0, y: 0, width: 0, height: 0 });
  assert.equal(f.native.at(-1)[1].width, 640);
  f.nodes.find(n => n.textContent === 'Cerrar').onclick();
  assert.equal(f.nodes.find(n => n.tag === 'dialog').isConnected, false);
});

test('missing native bridge fails closed rather than invoking the old terminal fallback', async () => {
  const f = fixture(undefined, false);
  assert.equal(await f.ipc.invoke('open_session', { sessionId: 'selected' }), false);
  assert.equal(f.native.filter(([command]) => command === 'open_session').length, 0);
  assert.ok(f.nodes.find(n => n.textContent?.includes('puente local')));
});

test('native immutable Tauri invoke reaches the routed handler with selected identity', async () => {
  const f = fixture(undefined, true, true);
  assert.equal(Object.getOwnPropertyDescriptor(f.ipc,'invoke').writable, false);
  assert.equal(await f.ipc.invoke('open_session', {agent:'hermes', sessionId:'native-selected'}), true);
  assert.equal(f.requests[0].agent, 'hermes');
  assert.equal(f.requests[0].sessionId, 'native-selected');
  assert.equal(f.native.filter(([command])=>command==='open_session').length, 0);
});


test('native chat uses CLI backend without invoking API-key chat and rejects double sends', async () => {
  let release;
  const f = fixture(async request => request.action === 'chat' ? await new Promise(resolve => {release=resolve;}) : {ok:true});
  const first = f.ipc.invoke('chat_send', {query:'hola $() 日本語',context:null});
  await assert.rejects(f.ipc.invoke('chat_send',{query:'doble'}), /respondiendo/);
  assert.equal(f.requests.length,1);
  assert.equal(f.requests[0].agent,'codex');
  assert.equal(f.requests[0].query,'hola $() 日本語');
  release({ok:true,text:'respuesta'});
  assert.equal((await first).text,'respuesta');
  assert.equal(f.native.filter(([cmd])=>cmd==='chat_send').length,0);
});

test('known adapter requests automatic background creation, with no association dialog', async () => {
  const f = fixture(async request => ({ok:request.action==='open'}));
  await f.ipc.invoke('open_session',{agent:'hermes',sessionId:'legacy-execution'});
  assert.equal(f.requests[0].autoCreate,true);
  assert.equal(f.requests[0].agent,'hermes');
  assert.equal(f.nodes.some(n=>n.tag==='dialog'),false);
});

test('Coucou prepares and queries Hub work without starting its native chat model', async () => {
  const f = fixture(async request => ({ok:true,text:'RUN-001 · pending'}));
  assert.equal((await f.ipc.invoke('chat_send',{query:'/tarea auto Revisar APA ñ'})).text,'RUN-001 · pending');
  assert.equal(f.requests[0].action,'work');
  assert.equal(f.requests[0].operation,'plan');
  assert.equal(f.requests[0].agent,null);
  assert.equal(f.requests[0].query,'Revisar APA ñ');
  await f.ipc.invoke('chat_send',{query:'/estado RUN-001'});
  assert.equal(f.requests[1].operation,'show');
  assert.equal(f.requests[1].id,'RUN-001');
  await f.ipc.invoke('chat_send',{query:'/tarea codex Implementar API'});
  assert.equal(f.requests[2].agent,'codex');
  assert.equal(f.requests.some(request=>request.action==='chat'),false);
});

test('an execution opens only through its explicit Hub execution identity', async () => {
  const f=fixture(async request=>({ok:true,text:'opened'}));
  await f.ipc.invoke('chat_send',{query:'/abrir EXEC-007'});
  assert.equal(f.requests[0].action,'work');
  assert.equal(f.requests[0].operation,'open-execution');
  assert.equal(f.requests[0].id,'EXEC-007');
  assert.equal(f.native.filter(([command])=>command==='chat_send'||command==='open_session').length,0);
});

test('Antigravity uses the same work and terminal contracts as the existing agents', async () => {
  const f=fixture(async request=>({ok:true,text:'prepared'}),true,false,'antigravity');
  await f.ipc.invoke('chat_send',{query:'/tarea antigravity Revisar cambios ñ'});
  assert.equal(f.requests[0].action,'work');
  assert.equal(f.requests[0].agent,'antigravity');
  assert.equal(f.requests[0].query,'Revisar cambios ñ');
  await f.ipc.invoke('open_session',{agent:'antigravity',sessionId:'exact-antigravity-id'});
  assert.equal(f.requests[1].agent,'antigravity');
  assert.equal(f.requests[1].sessionId,'exact-antigravity-id');
  assert.equal(f.native.filter(([cmd])=>cmd==='open_session').length,0);
  await f.ipc.invoke('chat_send',{query:'Hola Antigravity'});
  assert.equal(f.requests[2].action,'chat');
  assert.equal(f.requests[2].agent,'antigravity');
  await f.ipc.invoke('chat_reset',{});
  assert.equal(f.requests[3].action,'chat-reset');
  assert.equal(f.requests[3].agent,'antigravity');
});
