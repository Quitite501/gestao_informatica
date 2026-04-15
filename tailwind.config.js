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
        }
      }
    }
  },
  plugins: [require('@tailwindcss/forms')]
}
