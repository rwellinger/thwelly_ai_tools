import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/header/header.component';
import { FooterComponent } from '../../shared/footer/footer.component';
import { SongProfileComponent } from '../../song-profile/song-profile.component';

@Component({
  selector: 'app-song-profile-page',
  standalone: true,
  imports: [
    CommonModule,
    HeaderComponent,
    FooterComponent,
    SongProfileComponent
  ],
  templateUrl: './song-profile-page.component.html',
  styleUrl: './song-profile-page.component.scss'
})
export class SongProfilePageComponent {
}