(function () {
  const FORM_ID = 'form-chamado';
  const DRAFT_KEY = 'chamado_novo_rascunho_v1';
  const MAX_FILE_SIZE = 10 * 1024 * 1024;
  const ALLOWED_EXTENSIONS = [
    'pdf', 'png', 'jpg', 'jpeg', 'webp',
    'doc', 'docx', 'xls', 'xlsx', 'txt'
  ];

  let quillDescricao = null;
  let arquivosSelecionados = [];

  function qs(selector, root = document) {
    return root.querySelector(selector);
  }

  function qsa(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  }

  function fileExtension(name) {
    const parts = String(name || '').split('.');
    return parts.length > 1 ? parts.pop().toLowerCase() : '';
  }

  function showMessage(target, message, type) {
    if (!target) return;
    target.textContent = message || '';
    target.dataset.type = type || 'info';
    target.hidden = !message;
  }

  function initTomSelects() {
    if (!window.TomSelect) return;

    const form = qs('#' + FORM_ID);
    const usuariosUrl = form ? form.dataset.usuariosUrl : '';

    qsa('select.tom-select').forEach((select) => {
      if (select.tomselect) return;

      const placeholder = select.dataset.placeholder || 'Digite para buscar';
      const isSolicitante = select.classList.contains('tom-select-solicitante');

      const config = {
        create: false,
        allowEmptyOption: true,
        maxOptions: isSolicitante ? 50 : 1000,
        placeholder: placeholder,
        plugins: ['dropdown_input'],
        sortField: isSolicitante ? [] : { field: 'text', direction: 'asc' },
        render: {
          option: function (data, escape) {
            return '<div class="ts-option">' + escape(data.text) + '</div>';
          },
          item: function (data, escape) {
            return '<div>' + escape(data.text) + '</div>';
          },
          no_results: function () {
            return '<div class="no-results">Nenhum resultado encontrado</div>';
          },
          loading: function () {
            return '<div class="spinner">Buscando...</div>';
          }
        }
      };

      if (isSolicitante && usuariosUrl) {
        config.valueField = 'value';
        config.labelField = 'text';
        config.searchField = ['text'];
        config.shouldLoad = function (query) {
          return query.length >= 2;
        };
        config.load = function (query, callback) {
          const url = new URL(usuariosUrl, window.location.origin);
          url.searchParams.set('q', query);

          fetch(url.toString(), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
          })
            .then((response) => {
              if (!response.ok) throw new Error('Falha na busca de usuarios');
              return response.json();
            })
            .then((data) => callback(data.results || []))
            .catch(() => callback());
        };
      }

      new TomSelect(select, config);
    });
  }

  function initQuill(form) {
    const editor = qs('#editor-descricao');
    const hidden = qs('#hidden-descricao');

    if (!editor || !hidden || !window.Quill) return;

    quillDescricao = new Quill(editor, {
      theme: 'snow',
      placeholder: 'Descreva o problema ou solicitacao em detalhes...',
      modules: {
        toolbar: [
          [{ header: [1, 2, 3, false] }],
          ['bold', 'italic', 'underline', 'strike'],
          [{ color: [] }, { background: [] }],
          [{ list: 'ordered' }, { list: 'bullet' }],
          ['blockquote', 'code-block'],
          ['link'],
          ['clean']
        ]
      }
    });

    if (hidden.value) {
      quillDescricao.root.innerHTML = hidden.value;
    }

    editor.addEventListener('click', () => quillDescricao.focus());

    quillDescricao.on('text-change', () => {
      hidden.value = quillDescricao.root.innerHTML;
      salvarRascunho(form);
    });
  }

  function initTitulo(form) {
    const campo = qs('#id_titulo') || qs('input[name="titulo"]');
    const contador = qs('#contador-titulo');
    const erro = qs('#erro-titulo');

    if (!campo) return;

    const max = parseInt(campo.dataset.maxlength || campo.maxLength || '255', 10);

    function atualizar() {
      const atual = campo.value.length;
      if (contador) contador.textContent = atual + '/' + max;
      if (erro && campo.value.trim()) showMessage(erro, '', 'erro');
    }

    campo.addEventListener('input', () => {
      atualizar();
      salvarRascunho(form);
    });

    campo.addEventListener('keydown', function (e) {
      if (e.key === 'Tab' && !e.shiftKey && quillDescricao) {
        e.preventDefault();
        quillDescricao.focus();
      }
    });

    atualizar();
  }

  function validarTitulo() {
    const campo = qs('#id_titulo') || qs('input[name="titulo"]');
    const erro = qs('#erro-titulo');

    if (!campo) return true;

    if (!campo.value.trim()) {
      showMessage(erro, 'Informe o titulo do chamado.', 'erro');
      campo.focus();
      return false;
    }

    showMessage(erro, '', 'erro');
    return true;
  }

  function initAnexos() {
    const dropZone = qs('#drop-zone');
    const input = qs('#input-anexos');
    const lista = qs('#lista-anexos');
    const status = qs('#status-anexos');

    if (!dropZone || !input || !lista) return;

    function validarArquivo(file) {
      const ext = fileExtension(file.name);

      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        return 'Extensao nao permitida: ' + file.name;
      }

      if (file.size > MAX_FILE_SIZE) {
        return 'Arquivo acima de 10 MB: ' + file.name;
      }

      return '';
    }

    function sincronizarInput() {
      const dt = new DataTransfer();
      arquivosSelecionados.forEach((file) => dt.items.add(file));
      input.files = dt.files;
    }

    function renderizarLista() {
      lista.innerHTML = '';

      if (!arquivosSelecionados.length) {
        showMessage(status, '', 'info');
        return;
      }

      arquivosSelecionados.forEach((file, index) => {
        const li = document.createElement('li');
        li.className = 'chamado-anexo-item';
        li.innerHTML =
          '<span class="chamado-anexo-nome">' + file.name + '</span>' +
          '<span class="chamado-anexo-tamanho">' + formatBytes(file.size) + '</span>' +
          '<button type="button" class="chamado-anexo-remover" data-index="' + index + '">Remover</button>';
        lista.appendChild(li);
      });

      showMessage(
        status,
        arquivosSelecionados.length + ' anexo(s) selecionado(s).',
        'sucesso'
      );
    }

    function adicionarArquivos(files) {
      const erros = [];

      Array.from(files).forEach((file) => {
        const erro = validarArquivo(file);
        if (erro) {
          erros.push(erro);
          return;
        }

        const duplicado = arquivosSelecionados.some((item) => (
          item.name === file.name &&
          item.size === file.size &&
          item.lastModified === file.lastModified
        ));

        if (!duplicado) arquivosSelecionados.push(file);
      });

      sincronizarInput();
      renderizarLista();

      if (erros.length) {
        showMessage(status, erros.join(' | '), 'erro');
      }
    }

    dropZone.addEventListener('click', () => input.click());

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('is-dragover');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('is-dragover');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('is-dragover');
      adicionarArquivos(e.dataTransfer.files);
    });

    input.addEventListener('change', () => adicionarArquivos(input.files));

    lista.addEventListener('click', (e) => {
      const button = e.target.closest('[data-index]');
      if (!button) return;

      arquivosSelecionados.splice(Number(button.dataset.index), 1);
      sincronizarInput();
      renderizarLista();
    });
  }

  function initPrioridade(form) {
    const prioridade = qs('#id_prioridade');
    const badge = qs('#badge-prioridade');

    if (!prioridade || !badge) return;

    function atualizarBadge() {
      const label = prioridade.options[prioridade.selectedIndex]?.text || 'Prioridade';
      const value = prioridade.value || 'media';

      badge.textContent = label;
      badge.dataset.prioridade = value;
      atualizarSla(form);
      salvarRascunho(form);
    }

    prioridade.addEventListener('change', atualizarBadge);
    atualizarBadge();
  }

  function initCategoria(form) {
    const categoria = qs('#id_categoria');

    if (!categoria) return;

    categoria.addEventListener('change', () => {
      atualizarSla(form);
      salvarRascunho(form);
    });
  }

  function atualizarSla(form) {
    const box = qs('#sla-previsao');
    const categoria = qs('#id_categoria');
    const prioridade = qs('#id_prioridade');

    if (!box || !categoria || !prioridade || !form.dataset.slaUrl) return;
    if (!categoria.value || !prioridade.value) {
      box.textContent = 'Selecione categoria e prioridade para calcular o SLA previsto.';
      box.dataset.status = 'neutro';
      return;
    }

    const url = new URL(form.dataset.slaUrl, window.location.origin);
    url.searchParams.set('categoria', categoria.value);
    url.searchParams.set('prioridade', prioridade.value);

    box.textContent = 'Calculando SLA previsto...';
    box.dataset.status = 'carregando';

    fetch(url.toString(), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then((response) => {
        if (!response.ok) throw new Error('Falha ao calcular SLA');
        return response.json();
      })
      .then((data) => {
        box.textContent = 'SLA previsto: ' + data.prazo_texto + ' | Prazo estimado: ' + data.vencimento_formatado;
        box.dataset.status = 'ok';
      })
      .catch(() => {
        box.textContent = 'Nao foi possivel calcular o SLA previsto.';
        box.dataset.status = 'erro';
      });
  }

  function dadosRascunho() {
    return {
      solicitante: qs('#id_solicitante')?.value || '',
      titulo: qs('#id_titulo')?.value || '',
      categoria: qs('#id_categoria')?.value || '',
      prioridade: qs('#id_prioridade')?.value || '',
      descricao: quillDescricao ? quillDescricao.root.innerHTML : (qs('#hidden-descricao')?.value || '')
    };
  }

  function salvarRascunho(form) {
    if (!form || form.dataset.draft !== '1') return;
    localStorage.setItem(DRAFT_KEY, JSON.stringify(dadosRascunho()));
  }

  function restaurarRascunho(form) {
    if (!form || form.dataset.draft !== '1') return;
    if (form.dataset.hasErrors === '1') return;

    const raw = localStorage.getItem(DRAFT_KEY);
    if (!raw) return;

    let data = null;
    try {
      data = JSON.parse(raw);
    } catch {
      return;
    }

    ['solicitante', 'titulo', 'categoria', 'prioridade'].forEach((name) => {
      const field = qs('#id_' + name);
      if (!field || !data[name]) return;

      field.value = data[name];

      if (field.tomselect) {
        field.tomselect.setValue(data[name], true);
      }

      field.dispatchEvent(new Event('change', { bubbles: true }));
      field.dispatchEvent(new Event('input', { bubbles: true }));
    });

    if (data.descricao && quillDescricao) {
      quillDescricao.root.innerHTML = data.descricao;
      const hidden = qs('#hidden-descricao');
      if (hidden) hidden.value = data.descricao;
    }
  }

  function initLimpar(form) {
    const limpar = qs('#btn-limpar-formulario');
    if (!limpar) return;

    limpar.addEventListener('click', () => {
      localStorage.removeItem(DRAFT_KEY);
      form.reset();

      qsa('select.tom-select').forEach((select) => {
        if (select.tomselect) select.tomselect.clear(true);
      });

      if (quillDescricao) quillDescricao.setText('');

      arquivosSelecionados = [];
      const input = qs('#input-anexos');
      const lista = qs('#lista-anexos');
      const status = qs('#status-anexos');
      if (input) input.value = '';
      if (lista) lista.innerHTML = '';
      showMessage(status, '', 'info');

      initPrioridade(form);

      const foco = qs('#id_solicitante') || qs('#id_titulo');
      if (foco?.tomselect) foco.tomselect.focus();
      else if (foco) foco.focus();
    });
  }

  function initSubmit(form) {
    form.addEventListener('submit', (event) => {
      if (quillDescricao) {
        const hidden = qs('#hidden-descricao');
        if (hidden) hidden.value = quillDescricao.root.innerHTML;
      }

      if (!validarTitulo()) {
        event.preventDefault();
        return;
      }

      localStorage.removeItem(DRAFT_KEY);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    const form = qs('#' + FORM_ID);
    if (!form) return;

    initTomSelects();
    initQuill(form);
    initTitulo(form);
    initAnexos();
    initCategoria(form);
    initPrioridade(form);
    initLimpar(form);
    restaurarRascunho(form);
    initSubmit(form);

    const foco = qs('#id_solicitante') || qs('#id_titulo');
    if (foco?.tomselect) foco.tomselect.focus();
    else if (foco) foco.focus();
  });
})();
