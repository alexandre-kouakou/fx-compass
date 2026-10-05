import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// envDir '..' => the single project-root .env is shared with Django
export default defineConfig({
  plugins: [react(), tailwindcss()],
  envDir: '..',
})
