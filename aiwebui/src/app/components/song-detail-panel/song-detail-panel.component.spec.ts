import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SongDetailPanelComponent } from './song-detail-panel.component';

describe('SongDetailPanelComponent', () => {
  let component: SongDetailPanelComponent;
  let fixture: ComponentFixture<SongDetailPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SongDetailPanelComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SongDetailPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
