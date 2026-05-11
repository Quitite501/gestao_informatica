// Inicializa Quill com suporte a tabelas (quill-better-table)
// Uso: initQuillWithTable(editorId, hiddenId, placeholder)
function initQuillWithTable(editorId, hiddenId, placeholder) {
  if (!window.Quill || !window.QuillBetterTable) {
    console.error('Quill ou QuillBetterTable nao carregados');
    return null;
  }

  // Evitar registro duplo
  if (!Quill.imports['modules/better-table']) {
    Quill.register({ 'modules/better-table': QuillBetterTable });
  }

  const quill = new Quill('#' + editorId, {
    theme: 'snow',
    placeholder: placeholder || 'Descreva aqui...',
    modules: {
      table: false,
      'better-table': {
        operationMenu: {
          items: {
            unmergeCells: { text: 'Desagrupar células' }
          },
          color: { colors: ['#ffffff', '#f3f4f6', '#dbeafe', '#fef3c7', '#fee2e2'], text: 'Cor de fundo' }
        }
      },
      toolbar: {
        container: [
          [{ header: [1, 2, 3, false] }],
          ['bold', 'italic', 'underline', 'strike'],
          [{ color: [] }, { background: [] }],
          [{ list: 'ordered' }, { list: 'bullet' }],
          ['blockquote', 'code-block'],
          ['link', 'image'],
          ['table'],
          ['clean']
        ]
      },
      keyboard: {
        bindings: QuillBetterTable.keyboardBindings
      }
    }
  });

  // Botão tabela: inserir 3x3
  const toolbar = quill.getModule('toolbar');
  toolbar.addHandler('table', function () {
    const module = quill.getModule('better-table');
    if (module) module.insertTable(3, 3);
  });

  // Sincronizar com campo hidden
  const hidden = document.getElementById(hiddenId);
  if (hidden) {
    if (hidden.value) quill.root.innerHTML = hidden.value;

    quill.on('text-change', function () {
      hidden.value = quill.root.innerHTML;
    });
  }

  return quill;
}
