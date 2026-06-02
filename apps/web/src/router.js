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
  { path: '/buscar', component: () => import('./components/BuscarEngenheiros.vue'), meta: { requiresAuth: true } },
  { path: '/estimativa/:id', component: EstimativaWizard },
  { path: '/admin', component: AdminSync, meta: { requiresAuth: true } },
  {
    path: '/configuracoes',
    component: () => import('./components/Configuracoes.vue'),
    meta: { requiresAuth: true },
    redirect: '/configuracoes/perfil',
    children: [
      { path: 'perfil',         component: () => import('./components/settings/TabPerfil.vue') },
      { path: 'empresa',        component: () => import('./components/settings/TabEmpresa.vue') },
      { path: 'preferencias',   component: () => import('./components/settings/TabPreferencias.vue') },
      { path: 'vitrine',        component: () => import('./components/settings/TabVitrine.vue') },
      { path: 'parametros-eap', component: () => import('./components/settings/TabParametrosEAP.vue') },
      { path: 'contratos',      component: () => import('./components/ConfiguracoesContratos.vue') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) {
      next({ path: '/auth', query: { tipo: 'cliente', redirect: to.fullPath } })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
