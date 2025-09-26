import {Routes} from '@angular/router';
import { AuthGuard } from './guards/auth.guard';

export const routes: Routes = [
    {path: '', redirectTo: '/imagegen', pathMatch: 'full'},
    {
        path: 'login',
        loadComponent: () => import('./auth/login/login.component').then(m => m.LoginComponent)
    },
    {
        path: 'songgen',
        canActivate: [AuthGuard],
        loadComponent: () => import('./song-generator/song-generator.component').then(m => m.SongGeneratorComponent)
    },
    {
        path: 'songview',
        canActivate: [AuthGuard],
        loadComponent: () => import('./song-view/song-view.component').then(m => m.SongViewComponent)
    },
    {
        path: 'profile',
        canActivate: [AuthGuard],
        loadComponent: () => import('./components/user-profile/user-profile.component').then(m => m.UserProfileComponent)
    },
    {
        path: 'imagegen',
        canActivate: [AuthGuard],
        loadComponent: () => import('./image-generator/image-generator.component').then(m => m.ImageGeneratorComponent)
    },
    {
        path: 'imageview',
        canActivate: [AuthGuard],
        loadComponent: () => import('./image-view/image-view.component').then(m => m.ImageViewComponent)
    },
    {
        path: 'settings',
        canActivate: [AuthGuard],
        loadComponent: () => import('./settings/settings.component').then(m => m.SettingsComponent),
        children: [
            {
                path: 'prompt-templates',
                loadComponent: () => import('./settings/prompt-templates/prompt-templates.component').then(m => m.PromptTemplatesComponent)
            },
            {path: '', redirectTo: 'prompt-templates', pathMatch: 'full'}
        ]
    }
];
