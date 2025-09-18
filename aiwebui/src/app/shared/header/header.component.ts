import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import * as packageInfo from '../../../../package.json';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent {
  version = (packageInfo as any).version;
}
