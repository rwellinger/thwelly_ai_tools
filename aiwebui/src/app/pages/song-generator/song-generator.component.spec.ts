import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SongGeneratorComponent } from './song-generator.component';

describe('SongGeneratorComponent', () => {
  let component: SongGeneratorComponent;
  let fixture: ComponentFixture<SongGeneratorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SongGeneratorComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(SongGeneratorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
