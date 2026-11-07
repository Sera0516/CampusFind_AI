
import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private readonly http = inject(HttpClient);
  private readonly api = 'http://127.0.0.1:8000/auth';

  readonly isLoggedIn = signal(
    !!localStorage.getItem('campusfind_token')
  );

  register(data: RegisterRequest): Observable<unknown> {
    return this.http.post(`${this.api}/register`, data);
  }

  login(data: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.api}/login`, data).pipe(
      tap(response => {
        localStorage.setItem('campusfind_token', response.access_token);
        this.isLoggedIn.set(true);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('campusfind_token');
    this.isLoggedIn.set(false);
  }

  getToken(): string | null {
    return localStorage.getItem('campusfind_token');
  }
}
