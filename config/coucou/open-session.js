// Coucou's local Agent Hub terminal and native-agent chat integration.
(() => {
  const active = new Map();
  const identities = new Map(); // native session ID -> adapters; never "the last event"
  const inFlight = new Map();
  let installTimer;

  function install() {
    const ipc = window.__TAURI_INTERNALS__;
    const handler = window.webkit?.messageHandlers?.coucouAgentHub;
    if (!ipc) return false;
    if (ipc.coucouAgentHubInstalled) return true;
    ipc.coucouAgentHubInstalled = true;
    const invoke = (window.__coucouNativeInvoke || ipc.invoke).bind(ipc);
    let chatAgent = 'codex';
    try { chatAgent = window.localStorage?.getItem('coucou-chat-agent') || 'codex'; } catch {}
    if (chatAgent === 'gemini') chatAgent = 'antigravity';
    if (!['codex', 'hermes', 'antigravity'].includes(chatAgent)) chatAgent = 'codex';
    let chatBusy = false, activeRun = null;
    let modal = null, lastCollapsed = false, lastRect = null;
    const modalRect = () => { const r = modal.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; };
    const present = box => {
      modal = box; box.showModal();
      invoke('set_collapsed', { collapsed: false });
      invoke('set_island_rect', modalRect());
      invoke('focus_window', { focused: true });
    };
    const dismiss = box => {
      box.close(); box.remove();
      if (modal !== box) return;
      modal = null;
      invoke('set_collapsed', { collapsed: lastCollapsed });
      if (lastRect) invoke('set_island_rect', lastRect);
      invoke('focus_window', { focused: false });
    };
    const call = async request => {
      if (!handler) throw new Error('No está disponible el puente local de Agent Hub en Coucou. No se abrió ninguna conversación.');
      const result = await handler.postMessage(request);
      if (result.error) throw new Error(result.error);
      return result;
    };

    const callback = ipc.transformCallback(event => {
      const p = event.payload;
      if (!p || typeof p.session_id !== 'string' || !p.session_id) return;
      // The relay's documented default is Claude Code. No inference from cwd or UI labels.
      const agent = typeof p.coucou_agent === 'string' && p.coucou_agent ? p.coucou_agent : 'claude';
      const session = p.session_id;
      const agents = identities.get(session) || new Set();
      agents.add(agent);
      identities.set(session, agents);
      const identity = JSON.stringify([agent, session]);
      const name = p.hook_event_name;
      const running = ['UserPromptSubmit', 'PreToolUse', 'PermissionRequest'].includes(name);
      const stopped = ['Stop', 'Interrupt', 'SessionEnd'].includes(name);
      const previous = active.get(identity);
      if (!running && !stopped && name !== 'SessionStart' && !p.route) return;
      if (previous && previous.running === running && name !== 'SessionStart' && !p.route) return;
      // Serialize per execution so a slow route lookup cannot overwrite a later Stop.
      const queue = previous?.queue || Promise.resolve();
      const next = queue.catch(() => {}).then(() => call({ action: 'observe',
        agent, sessionId: session, event: name, ...(p.route ? { route: p.route } : {}) }));
      active.set(identity, { running: running || (!stopped && previous?.running), queue: next });
      next.catch(error => console.error('[Coucou Agent Hub metadata]', error));
    }, false);
    invoke('plugin:event|listen', { event: 'hook', target: { kind: 'Any' }, handler: callback })
      .catch(error => console.error('[Coucou Agent Hub observer]', error));

    const element = (tag, text, parent) => {
      const node = document.createElement(tag);
      if (text !== undefined) node.textContent = text;
      parent?.append(node);
      return node;
    };
    async function dialog(request, message) {
      const box = element('dialog');
      box.setAttribute('aria-label', 'Continuar conversación con Agent Hub');
      box.style.cssText = 'position:fixed;top:0;left:50%;transform:translateX(-50%);width:640px;max-height:310px;overflow:auto;margin:0;border:1px solid var(--hairline,#313244);border-radius:0 0 18px 18px;padding:18px;background:var(--card,#242438);color:var(--ink,#cdd6f4);font:13px var(--font,monospace);z-index:10000';
      document.body.append(box);
      const title = element('strong', message || 'Esta ejecución no tiene una conversación asociada.', box);
      title.style.display = 'block';
      element('p', 'Selecciona una conversación real. Solo se abrirá la ruta que elijas.', box);
      const agentSelect = element('select', undefined, box);
      const choice = element('select', undefined, box);
      const status = element('p', '', box);
      status.setAttribute('role', 'status');
      const controls = element('div', undefined, box);
      const confirm = element('button', 'Asociar y continuar', controls);
      const create = element('button', 'Nueva conversación…', controls);
      const cancel = element('button', 'Cancelar', controls);
      for (const select of [agentSelect, choice]) select.style.cssText = 'display:block;width:100%;margin:8px 0;padding:7px;background:#181825;color:inherit;border:1px solid #45475a;border-radius:6px';
      for (const button of [confirm, create, cancel]) button.style.cssText = 'padding:7px 10px;margin-right:7px;border-radius:6px;border:1px solid #45475a;background:#313244;color:inherit;cursor:pointer';
      let choices = [], projects = [], creating = false, busy = false;
      const option = (select, value, text) => {
        const node = element('option', text, select); node.value = value;
      };
      const refresh = async () => {
        choice.replaceChildren();
        option(choice, '', creating ? 'Elige un proyecto…' : 'Elige una conversación…');
        if (!agentSelect.value) return;
        status.textContent = 'Consultando Agent Hub…';
        try {
          const requestedAgent = agentSelect.value, requestedCreation = creating;
          const result = await call({ action: creating ? 'projects' : 'conversations', agent: requestedAgent });
          if (!box.isConnected || agentSelect.value !== requestedAgent || creating !== requestedCreation) return;
          if (creating) {
            projects = result.items;
            projects.forEach((p, i) => option(choice, String(i), `${p.name || p.idCarpeta} · ${p.idCarpeta || p.id}`));
          } else {
            choices = result.items.filter(c => c.route?.agente === agentSelect.value);
            choices.forEach((c, i) => option(choice, String(i), `${c.title || c.route.idMessage} · ${c.route.idMessage} · ${c.route.agente}`));
          }
          status.textContent = '';
        } catch (error) { status.textContent = error.message; }
      };
      option(agentSelect, '', 'Elige el agente de esta ejecución…');
      try {
        const agents = (await call({ action: 'agents' })).items;
        for (const agent of agents.filter(a => a.installed && (!request.agent || a.id === request.agent))) {
          option(agentSelect, agent.id, agent.name || agent.id);
        }
        if (request.agent) { agentSelect.value = request.agent; agentSelect.disabled = true; await refresh(); }
      } catch (error) { status.textContent = error.message; }
      agentSelect.onchange = refresh;
      present(box);
      return new Promise(resolve => {
        const close = result => { dismiss(box); resolve(result); };
        cancel.onclick = () => { if (!busy) close(null); };
        box.addEventListener('cancel', event => { event.preventDefault(); if (!busy) close(null); });
        create.onclick = () => {
          if (busy) return;
          creating = !creating;
          confirm.textContent = creating ? 'Crear conversación nueva y continuar' : 'Asociar y continuar';
          create.textContent = creating ? 'Elegir una existente' : 'Nueva conversación…';
          refresh();
        };
        confirm.onclick = async () => {
          if (busy || choice.value === '' || !agentSelect.value) return;
          busy = true;
          confirm.disabled = create.disabled = cancel.disabled = true;
          try {
            const selection = creating ? { action: 'new', confirmed: true,
              folder: projects[Number(choice.value)].idCarpeta || projects[Number(choice.value)].id }
              : { action: 'associate', route: choices[Number(choice.value)].route };
            const result = await call({ ...request, ...selection, agent: agentSelect.value });
            close(result.route);
          } catch (error) {
            status.textContent = error.message;
            // A new descriptor may already exist: never repeat creation after any error.
            if (creating) { creating = false; confirm.textContent = 'Asociar y continuar'; create.textContent = 'Nueva conversación…'; await refresh(); status.textContent = error.message; }
          } finally { busy = false; confirm.disabled = create.disabled = cancel.disabled = false; }
        };
      });
    }

    function report(error) {
      // A visible error within Coucou, not a console-only failure or terminal fallback.
      const box = element('dialog');
      box.style.cssText = 'position:fixed;top:0;margin:0 auto;max-width:620px;max-height:300px;padding:20px;border:1px solid #45475a;border-radius:0 0 16px 16px;background:var(--card,#242438);color:var(--ink,#cdd6f4);font:13px var(--font,monospace)';
      element('p', error.message, box);
      element('button', 'Cerrar', box).onclick = () => { dismiss(box); };
      box.addEventListener('cancel', event => { event.preventDefault(); dismiss(box); });
      document.body.append(box); present(box);
    }

    const routedInvoke = function(command, args, options) {
      if (command === 'set_collapsed') {
        lastCollapsed = args.collapsed;
        if (modal) return invoke(command, { collapsed: false }, options);
      }
      if (command === 'set_island_rect') {
        lastRect = args;
        if (modal) return invoke(command, modalRect(), options);
      }
      if (command === 'focus_window' && modal) return invoke(command, { focused: true }, options);
      if (command === 'chat_reset') {
        if (chatBusy) return Promise.reject(new Error('El agente todavía está respondiendo.'));
        return call({action:'chat-reset',agent:chatAgent}).then(() => invoke(command,args,options));
      }
      if (command === 'chat_send') {
        const query = args?.query?.trim() || '';
        const task = query.match(/^\/tarea(?:\s+(auto|codex|hermes|antigravity|architect|antigravity-architect))?\s+([\s\S]+)$/i);
        const control = query.match(/^\/(estado|ejecutar|cancelar)\s+(RUN-[0-9]{3,12})$/i);
        const openExecution = query.match(/^\/abrir\s+(EXEC-[0-9]{3,12})$/i);
        if (task || control || openExecution || query === '/tareas') {
          if (chatBusy) return Promise.reject(new Error('Ya hay una respuesta en curso.'));
          chatBusy = true;
          const operations = {estado:'show',ejecutar:'execute',cancelar:'cancel'};
          const request = task ? {action:'work',operation:'plan',query:task[2],agent:task[1]?.toLowerCase()==='auto' ? null : task[1]?.toLowerCase()==='architect' ? 'antigravity-architect' : task[1]?.toLowerCase() || chatAgent}
            : openExecution ? {action:'work',operation:'open-execution',id:openExecution[1]}
            : control ? {action:'work',operation:operations[control[1].toLowerCase()],id:control[2]}
            : {action:'work',operation:'list'};
          if (request.operation === 'execute') activeRun = request.id;
          window.__coucouWorkRefresh?.();
          return call(request).then(result => ({text:result.text})).finally(() => {
            chatBusy = false; activeRun = null; window.__coucouWorkRefresh?.();
          });
        }

        if (chatBusy) return Promise.reject(new Error('El agente ya está respondiendo.'));
        chatBusy = true;
        return call({action:'chat', agent:chatAgent, query:args?.query, context:args?.context})
          .then(result => ({text:result.text})).finally(() => { chatBusy = false; });
      }
      if (command !== 'open_session') return invoke(command, args, options);
      const request = { action: 'open', sessionId: args?.sessionId || null,
        agent: args?.agent || args?.agente || null, autoCreate: true, ...(args?.route ? { route: args.route } : {}) };
      if (!request.agent && request.sessionId) {
        const agents = identities.get(request.sessionId);
        if (agents?.size === 1) request.agent = [...agents][0];
      }
      const identity = JSON.stringify([request.agent, request.sessionId]);
      if (inFlight.has(identity)) return inFlight.get(identity);
      const operation = (async () => {
        // Finish the selected execution's observation before checking its lock/route.
        const observed = active.get(identity);
        if (observed) await observed.queue;
        let result = await call(request);
        if (result.needsAssociation) {
          const route = await dialog(request);
          if (!route) return false;
          result = await call({ ...request, route });
        }
        return result.ok === true;
      })().catch(error => { report(error); return false; }).finally(() => inFlight.delete(identity));
      inFlight.set(identity, operation);
      return operation;
    };
    if (typeof MutationObserver !== 'undefined') {
      let menu = null;
      const decorate = () => {
        const bar = document.querySelector('.chat-bar');
        let stop = document.querySelector('.coucou-stop-work');
        if (activeRun && bar && !stop) {
          stop = element('button', 'Detener', bar); stop.className = 'picker-chip coucou-stop-work';
          stop.type = 'button'; stop.title = 'Cancelar este run de Agent Hub';
          const cancelRun = activeRun;
          stop.onclick = async () => {
            stop.disabled = true;
            try { await call({action:'work',operation:'cancel',id:cancelRun}); }
            catch (error) { report(error); }
            finally { stop.disabled = false; }
          };
        } else if (!activeRun && stop) stop.remove();
        const button = document.querySelector('.model-btn');
        if (!button) { menu?.remove(); menu = null; return; }
        const label = button.querySelector('.model-name');
        const title = ({codex:'Codex',hermes:'Hermes',antigravity:'Antigravity'})[chatAgent];
        if (label && label.textContent !== title) label.textContent = title;
        button.title = 'Agente · sesión general de Coucou';
        if (button.dataset.coucouAgentPicker) return;
        button.dataset.coucouAgentPicker = 'true';
        button.addEventListener('click', event => {
          event.preventDefault(); event.stopImmediatePropagation();
          if (chatBusy) return;
          if (menu?.isConnected) { menu.remove(); menu = null; return; }
          menu = element('div'); menu.className = 'picker on';
          menu.style.cssText = 'display:flex;flex:none;background:var(--card-flat,#181825);color:var(--ink,#cdd6f4)';
          const chips = element('div', undefined, menu); chips.className = 'picker-chips';
          for (const agent of ['codex', 'hermes', 'antigravity']) {
            const chip = element('button', ({codex:'Codex',hermes:'Hermes',antigravity:'Antigravity'})[agent], chips);
            chip.className = 'picker-chip' + (chatAgent === agent ? ' on' : '');
            chip.onclick = () => {
              chatAgent = agent;
              try { window.localStorage?.setItem('coucou-chat-agent', agent); } catch {}
              menu.remove(); menu = null; decorate();
            };
          }
          const tasks = element('button', 'Tareas', chips); tasks.className = 'picker-chip';
          tasks.title = 'Preparar una tarea en Agent Hub';
          tasks.onclick = () => {
            const input = document.querySelector('.chat-input');
            if (input) { input.value = '/tarea '; input.focus(); }
            menu.remove(); menu = null;
          };
          button.closest('.chat-body')?.insertBefore(menu, button.closest('.model-row'));
        }, true);
      };
      window.__coucouWorkRefresh = decorate;
      new MutationObserver(decorate).observe(document.body, {childList:true, subtree:true});
      decorate();
    }
    window.__coucouAgentHubInvoke = routedInvoke;
    // Test/browser stand-ins may expose a writable property; native Tauri uses the bootstrap.
    const descriptor = Object.getOwnPropertyDescriptor(ipc, 'invoke');
    if (!window.__coucouNativeInvoke && (!descriptor || descriptor.writable)) ipc.invoke = routedInvoke;
    return true;
  }
  if (!install()) {
    let tries = 0;
    installTimer = setInterval(() => { if (install() || ++tries >= 100) clearInterval(installTimer); }, 50);
  }
})();
