import 'babel-polyfill';
import fromGenerator from './redux-saga-test';
import { assert } from 'chai';
import fs from 'fs';
import { call, cps, fork, put, race, select, take } from 'redux-saga/effects';
import { openFileSucceeded } from '../../actions/EditorActions';
import { remote } from 'electron';
import { openFileDialog,
         openFile,
         writeFile,
         getEditorState,
         saveFileDialog,
         saveFile } from '../sagas';

describe('filesystem sagas', () => {
  it('should yield effects for opening file', () => {
    const expect = fromGenerator(assert, openFile());
    expect.next().call(openFileDialog);
    expect.next('mock-path').cps(fs.readFile, 'mock-path', 'utf8');
    expect.next('mock-data').put(openFileSucceeded('mock-data', 'mock-path'));
    expect.next().returns();
  });

  it('should yield effects for writing file', () => {
    const expect = fromGenerator(assert, writeFile('mock-path', 'mock-code'));
    expect.next().cps(fs.writeFile, 'mock-path', 'mock-code');
    expect.next().put({
      type: 'SAVE_FILE_SUCCEEDED',
      code: 'mock-code',
      filepath: 'mock-path'
    });
    expect.next().returns();
  });

  it('should yield effects for saving file', () => {
    const action = {
      type: 'SAVE_FILE',
      saveAs: false
    };
    const expect = fromGenerator(assert, saveFile(action));
    expect.next().select(getEditorState);
    // follows to writeFile
    expect.next({
      filepath: 'mock-path',
      code: 'mock-code'
    }).cps(fs.writeFile, 'mock-path', 'mock-code');
  });

  it('should yield effects for saving file as (saveAs true)', () => {
    const action = {
      type: 'SAVE_FILE',
      saveAs: true
    };
    const expect = fromGenerator(assert, saveFile(action));
    expect.next().select(getEditorState);
    expect.next({
      filepath: 'mock-path',
      code: 'mock-code'
    }).call(saveFileDialog);
    // follows to writeFile
    expect.next('mock-new-path').cps(fs.writeFile, 'mock-new-path', 'mock-code');
  });

  it('should yield effects for saving file as (no filepath)', () => {
    const action = {
      type: 'SAVE_FILE',
      saveAs: false
    };
    const expect = fromGenerator(assert, saveFile(action));
    expect.next().select(getEditorState);
    expect.next({
      filepath: null,
      code: 'mock-code'
    }).call(saveFileDialog);
    // follows to writeFile
    expect.next('mock-path').cps(fs.writeFile, 'mock-path', 'mock-code');
  });
});

/* old tests below
describe('filesystem sagas', () => {
  it('should yield effects for opening file', () => {
    const gen = openFile();
    expect(gen.next().value)
          .to.deep.equal(call(openFileDialog));
    expect(gen.next('mock-path').value)
          .to.deep.equal(cps(fs.readFile, 'mock-path', 'utf8'));
    expect(gen.next('mock-data').value)
          .to.deep.equal(put(openFileSucceeded('mock-data', 'mock-path')));
    expect(gen.next()).to.deep.equal({ done: true, value: undefined });
  });

  it('should yield effects for writing file', () => {
    const gen = writeFile('mock-path', 'mock-code');
    expect(gen.next().value)
          .to.deep.equal(cps(fs.writeFile, 'mock-path', 'mock-code'));
    expect(gen.next().value)
          .to.deep.equal(put({
            type: 'SAVE_FILE_SUCCEEDED',
            code: 'mock-code',
            filepath: 'mock-path'
          }));
    expect(gen.next()).to.deep.equal({ done: true, value: undefined });
  });
});
*/
