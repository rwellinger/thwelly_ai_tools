import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { ProgressService, ProgressState } from '../../services/ui/progress.service';

@Component({
  selector: 'app-progress-overlay',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './progress-overlay.component.html',
  styleUrl: './progress-overlay.component.scss'
})
export class ProgressOverlayComponent implements OnInit, OnDestroy {
  progressState: ProgressState = {
    isVisible: false,
    message: '',
    detail: ''
  };

  private subscription?: Subscription;
  private progressService = inject(ProgressService);

  ngOnInit(): void {
    this.subscription = this.progressService.progress$.subscribe(
      state => this.progressState = state
    );
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }
}