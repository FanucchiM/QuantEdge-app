import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule
  ],
  template: `
    <div class="login-container">
      <mat-card class="login-card">
        <mat-card-header>
          <mat-card-title>Stock Analyzer</mat-card-title>
          <mat-card-subtitle>Stock Analysis System</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <p>Welcome to the automatic stock analysis system.</p>
          <button mat-raised-button color="primary" (click)="enter()" class="full-width">
            Enter Dashboard
          </button>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .login-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .login-card {
      width: 400px;
      padding: 20px;
      text-align: center;
    }
    .full-width {
      width: 100%;
      margin-top: 20px;
    }
  `]
})
export class LoginComponent {
  constructor(private router: Router) {}

  enter(): void {
    this.router.navigate(['/dashboard']);
  }
}
