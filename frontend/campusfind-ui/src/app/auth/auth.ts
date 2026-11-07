
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth.html',
  styleUrl: './auth.css'
})
export class Auth {

  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  isRegister = signal(
    this.route.snapshot.data['mode'] === 'register'
  );

  loading = signal(false);
  errorMessage = signal('');
  successMessage = signal('');

  name = '';
  email = '';
  password = '';
  confirmPassword = '';

  toggleMode(): void {
    const newMode = !this.isRegister();

    this.isRegister.set(newMode);
    this.errorMessage.set('');
    this.successMessage.set('');

    this.router.navigate([newMode ? '/register' : '/login']);
  }

  submit(): void {
    this.errorMessage.set('');
    this.successMessage.set('');

    if (!this.email.trim() || !this.password) {
      this.errorMessage.set('Please enter your email and password.');
      return;
    }

    if (this.isRegister()) {

      if (!this.name.trim()) {
        this.errorMessage.set('Please enter your name.');
        return;
      }

      if (this.password !== this.confirmPassword) {
        this.errorMessage.set('Passwords do not match.');
        return;
      }

      this.loading.set(true);

      this.authService.register({
        name: this.name.trim(),
        email: this.email.trim(),
        password: this.password
      }).subscribe({
        next: () => {
          this.loading.set(false);
          this.successMessage.set('Registration successful! Please log in.');
          this.isRegister.set(false);
          this.password = '';
          this.confirmPassword = '';
          this.router.navigate(['/login']);
        },
        error: error => {
          this.loading.set(false);
          this.errorMessage.set(
            error.error?.detail || 'Registration failed. Please try again.'
          );
        }
      });

      return;
    }

    this.loading.set(true);

    this.authService.login({
      email: this.email.trim(),
      password: this.password
    }).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigate(['/dashboard']);
      },
      error: error => {
        this.loading.set(false);
        this.errorMessage.set(
          error.error?.detail || 'Login failed. Check your credentials.'
        );
      }
    });
  }
}
