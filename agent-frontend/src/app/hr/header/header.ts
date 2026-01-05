import { Component } from '@angular/core';

@Component({
  selector: 'app-header',
  standalone: false,
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class Header {
  title = 'Burnout Prevention Agent';
  subtitle = 'AI-powered employee wellness monitoring system';
}
