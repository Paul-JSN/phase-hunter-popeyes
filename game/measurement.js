/* Joint whole-register Z readout. Every shot contributes to both correlators. */
const Measurement=(()=>{
  function sample(probabilities,outcomes,shots,rng=Math.random){
    if(!Number.isInteger(shots)||shots<1) throw new Error('Positive integer shots required');
    if(!probabilities.length||probabilities.length!==outcomes.length) throw new Error('Joint readout distribution required');
    let total=0;const cdf=probabilities.map(p=>{
      if(!Number.isFinite(p)||p<0) throw new Error('Invalid probability');
      return total+=p;
    });
    if(total<=0) throw new Error('Empty distribution');
    let a=0,b=0;
    for(let i=0;i<shots;i++){
      const u=rng()*total;let lo=0,hi=cdf.length-1;
      while(lo<hi){const mid=(lo+hi)>>1;if(u<cdf[mid])hi=mid;else lo=mid+1;}
      a+=outcomes[lo][0];b+=outcomes[lo][1];
    }
    return [a/shots,b/shots];
  }
  return {sample};
})();
if(typeof module!=='undefined')module.exports=Measurement;
