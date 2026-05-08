import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { inject as injectAnalytics } from '@vercel/analytics';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'QuantEdge';
  currentYear: number = new Date().getFullYear();

  ngOnInit(): void {
    // Initialize Vercel Web Analytics
    // Using environment-based mode detection since Angular doesn't expose standard NODE_ENV
    injectAnalytics({
      mode: environment.production ? 'production' : 'development',
      debug: !environment.production
    });
  }
}