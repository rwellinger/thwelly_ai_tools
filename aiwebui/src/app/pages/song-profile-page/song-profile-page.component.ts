import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../components/header/header.component';
import { FooterComponent } from '../../components/footer/footer.component';
import { SongProfileComponent } from '../song-profile/song-profile.component';

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