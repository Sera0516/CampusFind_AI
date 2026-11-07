
import { Routes } from '@angular/router';

import { Auth } from './auth/auth';
import { Dashboard } from './dashboard';
import { MyReports } from './my-reports/my-reports';
import { ItemDetails } from './item-details/item-details';
import { MyClaims } from './my-claims/my-claims';

import { authGuard } from './guards/auth.guard';
import { ReceivedClaims } from './received-claims/received-claims';

export const routes: Routes = [

  // Default route
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },

  // Login
  {
    path: 'login',
    component: Auth
  },

  // Register
  {
    path: 'register',
    component: Auth,
    data: { mode: 'register' }
  },

  // Student Dashboard
  {
    path: 'dashboard',
    component: Dashboard,
    canActivate: [authGuard]
  },

  // My Reports
  {
    path: 'my-reports',
    component: MyReports,
    canActivate: [authGuard]
  },

  // My Claims
  {
    path: 'my-claims',
    component: MyClaims,
    canActivate: [authGuard]
  },
  // Received Claims
  {
    path: 'received-claims',
    component: ReceivedClaims,
    canActivate: [authGuard]
  },

  // Item Details
  {
    path: 'item/:id',
    component: ItemDetails,
    canActivate: [authGuard]
  },

  // Unknown routes
  {
    path: '**',
    redirectTo: 'login'
  }

];
