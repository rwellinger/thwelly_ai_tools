import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { CdkDragDrop, DragDropModule, moveItemInArray } from '@angular/cdk/drag-drop';
import { Subject } from 'rxjs';

import {
  LyricArchitectureConfig,
  SongSection,
  SongSectionItem,
  SongSectionDefinition,
  AVAILABLE_SECTIONS
} from '../../models/lyric-architecture.model';
import { LyricArchitectureService } from '../../services/lyric-architecture.service';
import { NotificationService } from '../../services/ui/notification.service';
import { SongSectionDisplayPipe } from '../../pipes/song-section-display.pipe';

@Component({
  selector: 'app-lyric-architect-modal',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    DragDropModule,
    SongSectionDisplayPipe
  ],
  templateUrl: './lyric-architect-modal.component.html',
  styleUrl: './lyric-architect-modal.component.scss'
})
export class LyricArchitectModalComponent implements OnInit, OnDestroy {
  config: LyricArchitectureConfig = { sections: [], lastModified: new Date() };
  availableSections: SongSectionDefinition[] = AVAILABLE_SECTIONS;

  private destroy$ = new Subject<void>();

  private architectureService = inject(LyricArchitectureService);
  private notificationService = inject(NotificationService);
  private dialogRef = inject(MatDialogRef<LyricArchitectModalComponent>);

  ngOnInit(): void {
    this.loadConfig();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadConfig(): void {
    this.config = this.architectureService.getConfig();
  }

  onSectionDrop(event: CdkDragDrop<any>): void {
    if (event.previousContainer === event.container) {
      // Reordering within song structure
      moveItemInArray(this.config.sections, event.previousIndex, event.currentIndex);
      this.updateConfig();
    } else {
      // Adding new section from available sections
      const sectionDef = event.previousContainer.data[event.previousIndex] as SongSectionDefinition;
      const sectionType = sectionDef.section;
      this.addSection(sectionType);
    }
  }

  onAvailableSectionDrop(event: CdkDragDrop<SongSectionDefinition[]>): void {
    // Prevent dropping back to available sections
    if (event.previousContainer !== event.container) {
      return;
    }
  }

  addSection(section: SongSection): void {
    try {
      this.config = this.architectureService.addSection(section);
    } catch (error: any) {
      console.error('Error adding section:', error);
      this.notificationService.error(error.message);
    }
  }

  removeSection(itemId: string): void {
    try {
      this.config = this.architectureService.removeSection(itemId);
    } catch (error: any) {
      this.notificationService.error(`Error removing section: ${error.message}`);
    }
  }

  canAddSection(section: SongSection): boolean {
    return this.architectureService.canAddSection(section);
  }

  getSectionCount(section: SongSection): number {
    return this.architectureService.getSectionCount(section, this.config);
  }

  reset(): void {
    this.config = this.architectureService.resetToDefault();
    this.notificationService.success('Song architecture reset to default');
  }

  save(): void {
    try {
      this.architectureService.saveConfig(this.config);
      const architectureString = this.architectureService.generateArchitectureString(this.config);

      this.dialogRef.close({
        config: this.config,
        architectureString: architectureString
      });
    } catch (error: any) {
      this.notificationService.error(`Error saving configuration: ${error.message}`);
    }
  }

  cancel(): void {
    this.dialogRef.close();
  }

  private updateConfig(): void {
    try {
      const sectionIds = this.config.sections.map(s => s.id);
      this.config = this.architectureService.reorderSections(sectionIds);
    } catch (error: any) {
      this.notificationService.error(`Error updating configuration: ${error.message}`);
    }
  }

  getPreviewText(): string {
    return this.architectureService.generateArchitectureString(this.config);
  }

  // Drag & Drop helper methods
  noReturnPredicate(): boolean {
    return false;
  }

  trackBySectionId(index: number, item: SongSectionItem): string {
    return item.id;
  }

  getSectionDescription(section: SongSection): string {
    const sectionDef = AVAILABLE_SECTIONS.find(s => s.section === section);
    return sectionDef?.description || '';
  }
}