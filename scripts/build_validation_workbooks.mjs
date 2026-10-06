// Run a copy from a private tool directory with the bundled artifact-tool junction.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root=process.cwd(), stage=path.join(root,'research/data/validation-20261006');
const packets=JSON.parse(await fs.readFile(path.join(stage,'review/coordinator/packet-inputs.json'),'utf8'));
const labels=['phishing','genuine','out_of_scope','uncertain'];
const onlyPhone=process.argv.includes('--phone-only');
const safe=v=>typeof v==='string'&&/^[\s]*[=+@-]/.test(v)?"'"+v:v;
const previews=path.join(stage,'workbook-previews');await fs.mkdir(previews,{recursive:true});

function sheet(wb,name,headers,rows,widths){
  const s=wb.worksheets.add(name);s.showGridLines=false;
  const values=[headers,...rows].map(row=>row.map(safe));
  s.getRangeByIndexes(0,0,values.length,headers.length).values=values;
  const used=s.getRangeByIndexes(0,0,values.length,headers.length);
  used.format.font={name:'Arial',size:11,color:'#242424'};
  used.format.wrapText=true;used.format.rowHeight=38;used.format.verticalAlignment='top';
  const h=s.getRangeByIndexes(0,0,1,headers.length);
  h.format.fill='#26384B';h.format.font={name:'Arial',size:11,bold:true,color:'#FFFFFF'};h.format.rowHeight=42;
  widths.forEach((width,i)=>s.getRangeByIndexes(0,i,values.length,1).format.columnWidth=width);
  s.freezePanes.freezeRows(1);
  return s;
}
function guide(wb,rows){return sheet(wb,'Guide',['Step','Instructions'],rows,[25,100]);}
async function finish(wb,file,views){
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30}});
  // Inspect metadata/empty input columns only; never print private message text.
  await fs.writeFile(path.join(previews,path.basename(file)+'.inspection.json'),errors.ndjson);
  const output=await SpreadsheetFile.exportXlsx(wb);await output.save(file);
  for(const [name,range] of views){
    const preview=await wb.render({sheetName:name,range,scale:1.2,format:'png'});
    await fs.writeFile(path.join(previews,path.basename(file)+'-'+name+'.png'),new Uint8Array(await preview.arrayBuffer()));
  }
  console.log('Saved',path.basename(file));
}
const reviewGuide=[['Decide independently','Use the separate SMS labeling guide. Do not view inherited labels, rule categories, sources, model scores or another reviewer’s answers.'],
 ['Fill response fields','Choose phishing, genuine, out_of_scope or uncertain. Add a brief text-grounded rationale and privacy_issue: yes, no or uncertain. Leave unreviewed rows blank.'],
 ['Preserve the packet','Do not edit IDs or text. Flag any suspected personal information to the coordinator. Any text correction requires matched revised packets.'],
 ['Sign each completed row','Enter your reviewer code and the actual completed_at_utc timestamp, for example YYYY-MM-DDTHH:MM:SSZ.'],
 ['Return privately','Save the completed workbook and export only the Review sheet as UTF-8 CSV. Do not distribute the packet to other reviewers.'],
 ['No review claimed','All response cells start blank. Automated text minimization does not certify human privacy review.']];
for(const who of onlyPhone?[]:['a','b']){
  const wb=Workbook.create();
  const rows=packets.packets[who].map(r=>packets.fields.map(k=>r[k]??''));
  const s=sheet(wb,'Review',packets.fields,rows,[35,86,19,48,18,20,27]);
  s.getRange(`C2:G${rows.length+1}`).format.fill='#FFF6D9';
  s.getRange(`C2:C${rows.length+1}`).dataValidation={rule:{type:'list',values:labels}};
  s.getRange(`E2:E${rows.length+1}`).dataValidation={rule:{type:'list',values:['no','yes','uncertain']}};
  rows.forEach((row,i)=>s.getRangeByIndexes(i+1,0,1,7).format.rowHeight=Math.max(52,Math.ceil(String(row[1]).length/75)*15));
  guide(wb,reviewGuide);
  // Export the real private packet; preview its layout with fictional replacements only.
  const output=await SpreadsheetFile.exportXlsx(wb);const filename=path.join(stage,`review/annotator-${who}.xlsx`);await output.save(filename);
  const inspect=await wb.inspect({kind:'table',range:'Review!C1:G4',include:'values,formulas',tableMaxRows:4,tableMaxCols:5});
  await fs.writeFile(path.join(previews,`annotator-${who}-empty-fields.json`),inspect.ndjson);
  s.getRange('A2:B5').values=[['fictional-preview-1','Your account is suspended. Verify your password at https://account.example now.'],['fictional-preview-2','Bayad na po. Salamat sa tulong, kita tayo bukas.'],['fictional-preview-3','Your payment is received.'],['fictional-preview-4','A longer fictional preview sentence to verify that message text wraps clearly and remains readable during independent review.']];
  s.getRange('A2:G5').format.rowHeight=65;
  for(const [name,range] of [['Review','A1:G5'],['Guide','A1:B7']]){
    const p=await wb.render({sheetName:name,range,scale:1.2,format:'png'});
    await fs.writeFile(path.join(previews,`annotator-${who}-${name}.png`),new Uint8Array(await p.arrayBuffer()));
  }
  console.log('Saved blinded packet',who,rows.length,'rows; blank decisions verified in separate check.');
}
const intake=['intake_id','received_at_utc','collected_at_utc','redacted_text','collector_code','source_use_evidence','receipt_evidence_ref','permission_status','privacy_review_status','privacy_reviewer','prior_model_viewing','notes'];
if(!onlyPhone){
  await fs.mkdir(path.join(stage,'prospective'),{recursive:true});
  await fs.writeFile(path.join(stage,'prospective/intake.csv'),intake.join(',')+'\n',{flag:'wx'});
  const wb=Workbook.create();const s=sheet(wb,'Intake',intake,Array.from({length:20},()=>intake.map(()=>'')),[22,27,27,80,20,42,35,22,25,23,22,44]);
  s.getRange('A2:L21').format.fill='#FFF6D9';
  s.getRange('H2:H21').dataValidation={rule:{type:'list',values:['approved','pending','denied']}};
  s.getRange('I2:I21').dataValidation={rule:{type:'list',values:['verified','pending','failed']}};
  s.getRange('K2:K21').dataValidation={rule:{type:'list',values:['no','yes','unknown']}};
  guide(wb,[['Empty intake','No messages or human decisions are prefilled. Existing datasets and fictional examples are ineligible as newly collected data.'],['Dates','Use actual UTC receipt and collection times. Both must follow the recorded model freeze; receipt must precede collection.'],['Evidence','Use controlled evidence references, not sender identities or private screenshots in this workbook. Record the source-use basis and privacy reviewer.'],['Blinding','Collectors and reviewers must not use model results to select or label the new cohort.'],['Screening','Export the Intake sheet as UTF-8 CSV and run exact/near-history and within-intake checks before any predictions. No-match requires human semantic and evidence review.'],['Protocol','Follow the separately supplied prospective validation plan, including its stopping rule, grouping and locked-model policy.']]);
  await finish(wb,path.join(stage,'prospective/intake-template.xlsx'),[['Intake','A1:F4'],['Guide','A1:B7']]);
}
{
  const wb=Workbook.create();
  const fields=['tester_code','device_code','manufacturer_model','android_version','ram_if_known','free_storage_before','date_utc','battery_condition','test_order','network_state','evidence_folder_reference'];
  const d=sheet(wb,'Device',['Field','Actual observation'],fields.map(k=>[k,'']),[32,85]);d.getRange('B2:B12').format.fill='#FFF6D9';
  const install=sheet(wb,'Install',['algorithm','actual_apk_sha256','install_result','displayed_model_id','automatic_warnings_disabled','reporting_disabled','evidence_reference'],
    ['lr','nb','svm','mbert'].map(n=>[n,'','','','','','']),[14,70,34,40,32,26,42]);
  install.getRange('B2:G5').format.fill='#FFF6D9';
  const scanHeads=['algorithm','probe','input_route','actual_result','model_score','model_version','offline_confirmed','crash_or_issue','evidence_reference','tested_at_utc'];
  const scans=['lr','nb','svm','mbert'].flatMap(n=>['P1','P2','P3','P4','E1','E2','L1','P1-share'].map(p=>[n,p,p==='P1-share'?'share':'paste','','','','','','','']));
  const s=sheet(wb,'Scans',scanHeads,scans,[13,15,15,29,18,35,22,40,35,27]);s.getRange('D2:J33').format.fill='#FFF6D9';
  s.getRange('E2:E33').setNumberFormat('0.0%');
  const timings=['lr','nb','svm','mbert'].flatMap(n=>['cold','warm'].flatMap(kind=>Array.from({length:kind==='cold'?3:20},(_,i)=>[n,kind,i+1,kind==='warm'?`P${i%4+1}`:'launch','','','',''])));
  const t=sheet(wb,'Timing',['algorithm','measurement','trial','probe','elapsed_ms','measurement_method','evidence_reference','issue'],timings,[14,20,11,14,20,43,40,42]);t.getRange('E2:H93').format.fill='#FFF6D9';t.getRange('E2:E93').setNumberFormat('0.0');
  guide(wb,[['Status','Physical-device checks remain pending until actual returns and evidence are received. Prelisted algorithms/probes/trials are a plan, not measurements.'],['Network','Airplane mode on and Wi-Fi off. Record previous settings and restore them after testing.'],['Same fictional probes','Use the exact P1–P4, E1/E2 and L1 examples in the remote phone-test guide for all four APKs. Never use real SMS in this form.'],['Outcomes','Record actual results, scores, abstentions and crashes. Enter a percentage such as 97.6% in model_score, or leave blank when unavailable.'],['Timing','Three cold launches, then 20 warmups and 20 measured warm scans per app. Enter measured milliseconds and method; leave missing measurements blank.'],['Privacy','Use anonymous tester/device codes. No IMEI, account names, phone numbers or serial numbers. Share evidence through a controlled private channel.']]);
  await fs.mkdir(path.join(stage,'phone'),{recursive:true});
  await finish(wb,path.join(stage,'phone/physical-phone-results.xlsx'),[['Device','A1:B12'],['Install','A1:G5'],['Scans','A1:G5'],['Timing','A1:H6'],['Guide','A1:B7']]);
}
