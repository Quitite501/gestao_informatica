function initQuillWithTable(editorId, hiddenId, placeholder) {
  var Quill = window.Quill;
  if (!Quill) { console.error('Quill nao carregado'); return null; }

  var quill = new Quill('#' + editorId, {
    theme: 'snow',
    placeholder: placeholder || 'Descreva aqui...',
    modules: {
      clipboard: { matchVisual: false },
      toolbar: {
        container: [
          [{header: [1, 2, 3, false]}],
          ['bold', 'italic', 'underline', 'strike'],
          [{color: []}, {background: []}],
          [{list: 'ordered'}, {list: 'bullet'}],
          ['blockquote', 'code-block'],
          ['link', 'image'],
          ['clean']
        ]
      }
    }
  });

  function buildTable(rows, cols) {
    var s = 'border:1px solid #ccc;padding:6px 10px;text-align:left;';
    var hs = s + 'background:#f5f5f5;font-weight:600;';
    var html = '<table style="border-collapse:collapse;width:100%;margin:8px 0;">';
    html += '<thead><tr>';
    for (var c = 0; c < cols; c++) {
      html += '<th style="' + hs + '">Coluna ' + (c+1) + '</th>';
    }
    html += '</tr></thead><tbody>';
    for (var r = 0; r < rows; r++) {
      html += '<tr>';
      for (var c = 0; c < cols; c++) {
        html += '<td style="' + s + '">&nbsp;</td>';
      }
      html += '</tr>';
    }
    html += '</tbody></table>';
    return html;
  }

  function normalizeTable(tableEl) {
    tableEl.removeAttribute('class');
    tableEl.style.borderCollapse = 'collapse';
    tableEl.style.width = '100%';
    tableEl.style.margin = '8px 0';
    tableEl.querySelectorAll('td, th').forEach(function(cell) {
      cell.removeAttribute('class');
      cell.style.border = '1px solid #ccc';
      cell.style.padding = '6px 10px';
      cell.style.textAlign = cell.style.textAlign || 'left';
    });
    tableEl.querySelectorAll('tr').forEach(function(tr) {
      tr.removeAttribute('class');
    });
  }

  function insertHtmlAtCursor(html) {
    var editorEl = quill.root;
    editorEl.focus();
    var sel = window.getSelection();
    quill.getSelection(true);
    var frag = document.createRange().createContextualFragment(html + '<p><br></p>');
    var edRange;
    try { edRange = sel.getRangeAt(0); } catch(e) { edRange = null; }
    if (!edRange || !editorEl.contains(edRange.commonAncestorContainer)) {
      edRange = document.createRange();
      edRange.selectNodeContents(editorEl);
      edRange.collapse(false);
    }
    edRange.deleteContents();
    edRange.insertNode(frag);
    sel.collapseToEnd();
    quill.update();
    var hidden = document.getElementById(hiddenId);
    if (hidden) hidden.value = quill.root.innerHTML;
  }

  quill.root.addEventListener('paste', function(e) {
    var cd = e.clipboardData || window.clipboardData;
    var html = cd.getData('text/html');
    if (html && html.indexOf('<table') !== -1) {
      e.preventDefault();
      e.stopPropagation();
      var doc = new DOMParser().parseFromString(html, 'text/html');
      doc.querySelectorAll('table').forEach(normalizeTable);
      insertHtmlAtCursor(doc.body.innerHTML);
    }
  }, true);

  var toolbar = quill.container.previousElementSibling;
  if (toolbar) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.title = 'Inserir tabela 3x3';
    btn.className = 'ql-table-custom';
    btn.style.cssText = 'width:28px;height:24px;padding:2px;cursor:pointer;border:none;' +
      'background:transparent;display:inline-flex;align-items:center;' +
      'justify-content:center;vertical-align:middle;opacity:0.75;';
    btn.innerHTML = '<svg viewBox="0 0 18 18" width="15" height="15">' +
      '<rect x="1" y="1" width="7" height="7" rx="0.5" fill="none" stroke="currentColor" stroke-width="1.5"/>' +
      '<rect x="10" y="1" width="7" height="7" rx="0.5" fill="none" stroke="currentColor" stroke-width="1.5"/>' +
      '<rect x="1" y="10" width="7" height="7" rx="0.5" fill="none" stroke="currentColor" stroke-width="1.5"/>' +
      '<rect x="10" y="10" width="7" height="7" rx="0.5" fill="none" stroke="currentColor" stroke-width="1.5"/>' +
      '</svg>';
    btn.onmouseover = function() { this.style.opacity = '1'; };
    btn.onmouseout = function() { this.style.opacity = '0.75'; };
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      insertHtmlAtCursor(buildTable(3, 3));
    });
    var cleanBtn = toolbar.querySelector('.ql-clean');
    if (cleanBtn && cleanBtn.parentNode) {
      cleanBtn.parentNode.insertBefore(btn, cleanBtn);
    } else {
      var lastGroup = toolbar.querySelector('.ql-formats:last-child');
      if (lastGroup) lastGroup.appendChild(btn);
      else toolbar.appendChild(btn);
    }
  }

  var hidden = document.getElementById(hiddenId);
  if (hidden) {
    if (hidden.value) quill.root.innerHTML = hidden.value;
    quill.on('text-change', function() { hidden.value = quill.root.innerHTML; });
  }

  return quill;
}
