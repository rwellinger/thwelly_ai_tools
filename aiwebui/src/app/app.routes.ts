import {Routes} from '@angular/router';

export const routes: Routes = [
    {path: '', redirectTo: '/imagegen', pathMatch: 'full'},
    {
        path: 'songgen',
        loadComponent: () => import('./song-generator/song-generator.component').then(m => m.SongGeneratorComponent)
    },
    {
        path: 'songview',
        loadComponent: () => import('./song-view/song-view.component').then(m => m.SongViewComponent)
    },
    {
        path: 'songprof',
        loadComponent: () => import('./song-profile/song-profile.component').then(m => m.SongProfileComponent)
    },
    {
        path: 'imagegen',
        loadComponent: () => import('./image-generator/image-generator.component').then(m => m.ImageGeneratorComponent)
    },
    {
        path: 'imageview',
        loadComponent: () => import('./image-view/image-view.component').then(m => m.ImageViewComponent)
    }
];
