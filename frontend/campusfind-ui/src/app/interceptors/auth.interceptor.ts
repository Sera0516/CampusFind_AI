
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

const API_URL = 'http://127.0.0.1:8000';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);

  if (!req.url.startsWith(API_URL)) {
    return next(req);
  }

  const token = localStorage.getItem('campusfind_token');

  const authenticatedRequest = token
    ? req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      })
    : req;

  return next(authenticatedRequest).pipe(
    catchError(error => {
      if (error.status === 401 && !req.url.includes('/auth/login')) {
        localStorage.removeItem('campusfind_token');
        router.navigate(['/login']);
      }

      return throwError(() => error);
    })
  );
};
