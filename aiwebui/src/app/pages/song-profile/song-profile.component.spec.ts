import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SongProfileComponent } from './song-profile.component';

describe('SongProfileComponent', () => {
  let component: SongProfileComponent;
  let fixture: ComponentFixture<SongProfileComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SongProfileComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(SongProfileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
