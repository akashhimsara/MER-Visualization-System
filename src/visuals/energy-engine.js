import * as THREE from 'three';

const TAU = Math.PI * 2;

function createPath(angle, index, primary, secondary) {
  const side = new THREE.Vector3(Math.cos(angle), Math.sin(angle), 0);
  const bend = new THREE.Vector3(-Math.sin(angle), Math.cos(angle), 0);
  const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 0, 0),
    side.clone().multiplyScalar(1.2).add(bend.clone().multiplyScalar((index % 2 ? 1 : -1) * .7)).setZ(-.3),
    side.clone().multiplyScalar(3.4).add(bend.clone().multiplyScalar((index % 2 ? 1 : -1) * 1.25)).setZ(-.7),
    side.clone().multiplyScalar(6.0).add(bend.clone().multiplyScalar((index % 2 ? 1 : -1) * .35)).setZ(-1.2)
  ]);
  // A thin tube reads as an intentional energy conduit. A WebGL line is only
  // one pixel wide and becomes visual noise once bloom is enabled.
  const line = new THREE.Mesh(
    new THREE.TubeGeometry(curve, 96, .018, 6, false),
    new THREE.MeshBasicMaterial({ color: index % 2 ? primary : secondary, transparent: true, opacity: .28, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  const pulses = Array.from({ length: 4 }, (_, pulseIndex) => {
    const node = new THREE.Mesh(new THREE.SphereGeometry(.075, 12, 8), new THREE.MeshBasicMaterial({ color: index % 2 ? primary : secondary, transparent: true, opacity: .94, blending: THREE.AdditiveBlending, depthWrite: false }));
    return { node, offset: pulseIndex / 4 + index * .071 };
  });
  return { curve, line, pulses };
}

/** Procedural story visual: a music-energy heart sending pulses through luminous channels. */
export function createEnergyEngine() {
  const group = new THREE.Group(); group.name = 'mode_energyEngine'; group.position.y = 1.45;
  const primary = new THREE.Color(0x23e8ff), secondary = new THREE.Color(0xff4cc9);
  // Unlit materials protect the core's identity from the scene's moving lights.
  // Previously the StandardMaterial + bloom clipped the entire object to white.
  const core = new THREE.Mesh(new THREE.IcosahedronGeometry(.86, 4), new THREE.MeshBasicMaterial({ color: primary, transparent: true, opacity: .72, depthWrite: false })); group.add(core);
  const innerCore = new THREE.Mesh(new THREE.IcosahedronGeometry(.48, 3), new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: .32, depthWrite: false })); group.add(innerCore);
  const coreShell = new THREE.Mesh(new THREE.IcosahedronGeometry(1.28, 2), new THREE.MeshBasicMaterial({ color: secondary, wireframe: true, transparent: true, opacity: .08, blending: THREE.AdditiveBlending, depthWrite: false })); group.add(coreShell);
  // Four satellites give the viewer a readable story: the seed sends energy
  // outward, the satellites receive it, then the system releases it again.
  const paths=[];
  for(let i=0;i<4;i++){const path=createPath((i/4)*TAU,i,primary,secondary);group.add(path.line);path.pulses.forEach(p=>group.add(p.node));paths.push(path);}
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1.62,.025,8,96),new THREE.MeshBasicMaterial({color:primary,transparent:true,opacity:.65,blending:THREE.AdditiveBlending,depthWrite:false}));ring.rotation.x=.62;group.add(ring);
  const haloRings = [1.28, 1.82, 2.35].map((radius, index) => {
    const halo = new THREE.Mesh(new THREE.TorusGeometry(radius, .010, 6, 96), new THREE.MeshBasicMaterial({ color: index % 2 ? secondary : primary, transparent: true, opacity: .04, blending: THREE.AdditiveBlending, depthWrite: false }));
    halo.rotation.set(.52 + index * .34, index * .6, index * .38);
    group.add(halo);
    return halo;
  });
  group.userData={core,innerCore,coreShell,paths,ring,haloRings,primary,secondary}; return group;
}

export function updateEnergyEngine(group, frequencyData, dt=.016, time=0, beat=0, chapter={key:'FLOW',intensity:.2}) {
  if(!group?.userData)return; const {core,innerCore,coreShell,paths,ring,haloRings=[]}=group.userData; let bass=beat,mid=.18,high=.12;
  if(frequencyData?.length){const b=Math.max(1,Math.floor(frequencyData.length*.16)),h=Math.floor(frequencyData.length*.58);let bs=0,ms=0,hs=0;for(let i=0;i<b;i++)bs+=frequencyData[i];for(let i=b;i<h;i++)ms+=frequencyData[i];for(let i=h;i<frequencyData.length;i++)hs+=frequencyData[i];bass=Math.max(beat,bs/(b*255));mid=ms/Math.max(1,(h-b)*255);high=hs/Math.max(1,(frequencyData.length-h)*255);}
  const chapterKey=chapter.key||'FLOW';
  const surge=chapterKey==='SURGE'?1:0, build=chapterKey==='BUILD'?1:0, dormant=chapterKey==='DORMANT'?1:0, release=chapterKey==='RELEASE'?1:0;
  // Story states: seed sleeps, wakes, gathers, blooms at a drop, then exhales.
  const storyScale = dormant ? .58 : release ? .82 : build ? 1.02 : surge ? 1.15 : .88;
  const scale=storyScale+bass*.14+beat*.10; core.scale.setScalar(scale); innerCore.scale.setScalar(storyScale*.92+bass*.06); coreShell.scale.setScalar(storyScale*(.96+mid*.10+surge*.06)); core.rotation.y+=dt*(.10+mid*.38+surge*.28); core.rotation.x=time*.06;
  innerCore.rotation.y=-time*.12; core.material.opacity=.44+bass*.12+surge*.08-dormant*.16; innerCore.material.opacity=.14+bass*.08+surge*.08; coreShell.material.opacity=.025+high*.065+surge*.055;
  ring.rotation.z+=dt*(.18+mid*.48+surge*.48); ring.scale.setScalar(storyScale*(1+beat*.16+build*.06)); ring.material.opacity=.12+high*.16+surge*.14-dormant*.08;
  haloRings.forEach((halo,index)=>{const wave=Math.sin(time*(.42+index*.1)+index)*.035; halo.rotation.z+=dt*(index%2?-.09:.11)*(1+mid+surge); halo.scale.setScalar(1+wave+surge*(.05+index*.025)); halo.material.opacity=(dormant ? .012 : release ? .05 : .025)+high*.045+build*.035+surge*(.10+index*.03);});
  paths.forEach((path,index)=>{const pathLife=dormant ? .05 : release ? .11 : .16;path.line.material.opacity=pathLife+mid*.13+surge*.12;path.line.rotation.z=Math.sin(time*.28+index)*.018*(1+mid);path.pulses.forEach(p=>{const speed=.075+mid*.12+surge*.13;const t=(time*speed+p.offset)%1; p.node.position.copy(path.curve.getPoint(t));const pScale=(dormant ? .22 : .34)+bass*.38+beat*.26+surge*.18;p.node.scale.setScalar(pScale);p.node.material.opacity=dormant ? .12 : release ? .42 : .86;});});
}

export function setEnergyEngineColors(group, primaryValue, secondaryValue) {
  if(!group?.userData||primaryValue===undefined)return;const{core,innerCore,coreShell,paths,ring,haloRings=[],primary,secondary}=group.userData;primary.set(primaryValue);secondary.set(secondaryValue??new THREE.Color(primaryValue).offsetHSL(.44,.05,.04));core.material.color.copy(primary);innerCore.material.color.copy(secondary);coreShell.material.color.copy(secondary);ring.material.color.copy(primary);haloRings.forEach((halo,index)=>halo.material.color.copy(index%2?secondary:primary));paths.forEach((path,index)=>{const c=index%2?primary:secondary;path.line.material.color.copy(c);path.pulses.forEach(p=>p.node.material.color.copy(c));});
}
