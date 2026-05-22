import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './components/Dashboard.vue'
import Orcamento from './components/Orcamento.vue'
import EngenhariaList from './components/EngenhariaList.vue'
import PortalCliente from './components/PortalCliente.vue'
import AdminSync from './components/AdminSync.vue'
import Auth from './components/Auth.vue'
import EstimativaWizard from './components/EstimativaWizard.vue'
import LandingSimulador from './components/LandingSimulador.vue'
import { supabase } from './supabase'

const routes = [
  { path: '/auth', component: Auth },
  { path: '/', component: () => import('./components/LandingPage.vue') },
  { path: '/simulador', component: LandingSimulador },
  { path: '/dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/engenharia', component: EngenhariaList, meta: { requiresAuth: true } },
  { path: '/orcamento', redirect: '/engenharia' },
  { path: '/orcamento/:id', component: Orcamento, meta: { requiresAuth: true } },
  { path: '/portal/:token', component: PortalCliente },
  { path: '/p/:slug', component: () => import('./components/VitrinePublica.vue') },
  { path: '/estimativa/:id', component: EstimativaWizard },
  { path: '/admin', component: AdminSync, meta: { requiresAuth: true } },
  {
    path: '/configuracoes',
    component: () => import('./components/Configuracoes.vue'),
    meta: { requiresAuth: true }
  },
  { path: '/configuracoes/:tab', redirect: '/configuracoes' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  if (to.meta.requiresAuth) {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) {
      next('/auth')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
