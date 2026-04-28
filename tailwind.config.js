module.exports = {
  darkMode: 'class',
  content: ['./templates/**/*.html'],
  safelist: [
    'badge-aberto',
    'badge-em_atendimento',
    'badge-aguardando_usuario',
    'badge-encerrado',
    'badge-disponivel',
    'badge-em_uso',
    'badge-em_manutencao',
    'badge-baixado',
    'badge-critica',
    'badge-alta',
    'badge-media',
    'badge-baixa',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff', 100: '#dbeafe', 500: '#3b82f6',
          600: '#2563eb', 700: '#1d4ed8', 800: '#1e40af', 900: '#1e3a8a'
        },
        theme: {
          bg: 'var(--bg)',
          surface: 'var(--surface)',
          'surface-alt': 'var(--surface-alt)',
          border: 'var(--border)',
          'border-light': 'var(--border-light)',
        },
        tx: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          hover: 'var(--accent-hover)',
          text: 'var(--accent-text)',
        },
        status: {
          success: 'var(--success)',
          'success-bg': 'var(--success-bg)',
          'success-text': 'var(--success-text)',
          warning: 'var(--warning)',
          'warning-bg': 'var(--warning-bg)',
          'warning-text': 'var(--warning-text)',
          danger: 'var(--danger)',
          'danger-bg': 'var(--danger-bg)',
          'danger-text': 'var(--danger-text)',
          'info-bg': 'var(--info-bg)',
          'info-text': 'var(--info-text)',
        },
      },
      backgroundColor: {
        sidebar: 'var(--sidebar-bg)',
        'sidebar-hover': 'var(--sidebar-hover)',
        'sidebar-active': 'var(--sidebar-active-bg)',
        topbar: 'var(--topbar-bg)',
        'table-header': 'var(--table-header-bg)',
        'table-row-hover': 'var(--table-row-hover)',
        input: 'var(--input-bg)',
      },
      textColor: {
        sidebar: 'var(--sidebar-text)',
        'sidebar-active': 'var(--sidebar-active-text)',
        'table-header': 'var(--table-header-text)',
        input: 'var(--input-text)',
        'input-placeholder': 'var(--input-placeholder)',
      },
      borderColor: {
        topbar: 'var(--topbar-border)',
        table: 'var(--table-border)',
        input: 'var(--input-border)',
        'input-focus': 'var(--input-focus)',
      },
      ringColor: {
        'input-focus': 'var(--input-focus)',
      },
    }
  },
  plugins: [require('@tailwindcss/forms')]
}
