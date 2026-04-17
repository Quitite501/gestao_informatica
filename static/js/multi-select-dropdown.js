// Componente Dropdown com Checkboxes — suporte a tema claro/escuro
class MultiSelectDropdown {
    constructor(selectElement) {
        this.selectElement = selectElement;
        this.options = Array.from(selectElement.options);
        this.container = null;
        this.button = null;
        this.dropdown = null;
        this.isOpen = false;
        this.init();
    }
    
    init() {
        this.createDropdown();
        this.selectElement.style.display = 'none';
        this.selectElement.parentNode.insertBefore(this.container, this.selectElement.nextSibling);
        this.button.addEventListener('click', (e) => { e.preventDefault(); this.toggle(); });
        document.addEventListener('click', (e) => this.handleOutsideClick(e));
        this.updateButtonText();
    }
    
    isDark() {
        return document.documentElement.classList.contains('dark');
    }
    
    getColors() {
        const dark = this.isDark();
        return {
            bg:          dark ? 'rgb(17, 24, 39)'   : 'rgb(255, 255, 255)',
            bgHover:     dark ? 'rgb(31, 41, 55)'   : 'rgb(249, 250, 251)',
            border:      dark ? 'rgb(75, 85, 99)'   : 'rgb(209, 213, 219)',
            borderFocus: 'rgb(59, 130, 246)',
            text:        dark ? 'rgb(209, 213, 219)' : 'rgb(55, 65, 81)',
            placeholder: dark ? 'rgb(107, 114, 128)' : 'rgb(156, 163, 175)',
            dropBg:      dark ? 'rgb(17, 24, 39)'   : 'rgb(255, 255, 255)',
            dropHover:   dark ? 'rgb(31, 41, 55)'   : 'rgb(243, 244, 246)',
            dropShadow:  dark ? '0 10px 25px rgba(0,0,0,0.4)' : '0 10px 25px rgba(0,0,0,0.1)',
        };
    }
    
    applyTheme() {
        const c = this.getColors();
        this.button.style.background = this.isOpen ? c.bgHover : c.bg;
        this.button.style.borderColor = this.isOpen ? c.borderFocus : c.border;
        this.button.style.color = c.text;
        this.dropdown.style.background = c.dropBg;
        this.dropdown.style.borderColor = c.border;
        this.dropdown.style.boxShadow = c.dropShadow;
        
        this.dropdown.querySelectorAll('label').forEach(label => {
            label.style.color = c.text;
        });
        
        this.updateButtonText();
    }
    
    createDropdown() {
        const c = this.getColors();
        
        this.container = document.createElement('div');
        this.container.style.cssText = 'position: relative; width: 100%; min-width: 160px;';
        
        this.button = document.createElement('button');
        this.button.type = 'button';
        this.button.style.cssText = 'width: 100%; padding: 7px 12px; background: ' + c.bg + '; border: 1px solid ' + c.border + '; border-radius: 0.5rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.875rem; cursor: pointer; transition: border-color 0.15s, background 0.15s; color: ' + c.text + '; line-height: 1.25rem;';
        
        this.button.innerHTML = '<span class="dropdown-text" style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"></span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="flex-shrink: 0; margin-left: 8px; opacity: 0.5;"><path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5"/></svg>';
        
        this.dropdown = document.createElement('div');
        this.dropdown.style.cssText = 'position: absolute; top: calc(100% + 4px); left: 0; min-width: 100%; width: max-content; background: ' + c.dropBg + '; border: 1px solid ' + c.border + '; border-radius: 0.5rem; padding: 6px; box-shadow: ' + c.dropShadow + '; z-index: 9999; display: none; max-height: 280px; overflow-y: auto;';
        
        this.options.forEach((option) => {
            const label = document.createElement('label');
            label.style.cssText = 'display: flex; align-items: center; gap: 8px; padding: 6px 10px; cursor: pointer; font-size: 0.875rem; border-radius: 0.375rem; color: ' + c.text + '; white-space: nowrap; transition: background 0.15s;';
            
            const hoverColor = c.dropHover;
            label.addEventListener('mouseenter', () => { label.style.background = hoverColor; });
            label.addEventListener('mouseleave', () => { label.style.background = 'transparent'; });
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = option.value;
            checkbox.checked = option.selected;
            checkbox.style.cssText = 'width: 15px; height: 15px; cursor: pointer; border-radius: 0.25rem; accent-color: rgb(59, 130, 246);';
            
            checkbox.addEventListener('change', (e) => {
                e.stopPropagation();
                option.selected = checkbox.checked;
                this.updateButtonText();
            });
            
            const span = document.createElement('span');
            span.textContent = option.text;
            
            label.appendChild(checkbox);
            label.appendChild(span);
            this.dropdown.appendChild(label);
        });
        
        this.container.appendChild(this.button);
        this.container.appendChild(this.dropdown);
        
        // Observar mudança de tema
        const observer = new MutationObserver(() => this.applyTheme());
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    }
    
    updateButtonText() {
        const selected = this.options.filter(opt => opt.selected);
        const textSpan = this.button.querySelector('.dropdown-text');
        const c = this.getColors();
        
        if (selected.length === 0) {
            textSpan.textContent = 'Selecione...';
            textSpan.style.color = c.placeholder;
        } else if (selected.length === 1) {
            textSpan.textContent = selected[0].text;
            textSpan.style.color = c.text;
        } else {
            textSpan.textContent = selected.length + ' selecionados';
            textSpan.style.color = c.text;
        }
    }
    
    toggle() {
        this.isOpen = !this.isOpen;
        this.dropdown.style.display = this.isOpen ? 'block' : 'none';
        
        const c = this.getColors();
        this.button.style.borderColor = this.isOpen ? c.borderFocus : c.border;
        this.button.style.background = this.isOpen ? c.bgHover : c.bg;
    }
    
    handleOutsideClick(e) {
        if (!this.container.contains(e.target) && this.isOpen) {
            this.toggle();
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const multiSelects = document.querySelectorAll('select[multiple].multi-select-dropdown');
    multiSelects.forEach(select => new MultiSelectDropdown(select));
});
