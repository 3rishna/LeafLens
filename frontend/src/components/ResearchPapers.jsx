import React from 'react';
import { motion } from 'framer-motion';
import { BookOpen, ExternalLink, Dna, Layers, FileText } from 'lucide-react';

export default function ResearchPapers() {
  const papers = [
    {
      author: 'Caine et al. (2019)',
      title: 'Rice plants with reduced stomatal density exhibit improved water-use efficiency and drought tolerance',
      journal: 'New Phytologist',
      gene: 'OsEPF1 Overexpression',
      doi: '10.1111/nph.15344',
      url: 'https://doi.org/10.1111/nph.15344',
      contrib: '15 digitized measurements (IR64 cultivar)'
    },
    {
      author: 'Karavolias et al. (2023)',
      title: 'Paralogous OsEPFL genes modulate stomatal density in rice',
      journal: 'Plant Physiology',
      gene: 'OsEPFL9/10 Knockout',
      doi: '10.1093/plphys/kiad183',
      url: 'https://doi.org/10.1093/plphys/kiad183',
      contrib: '30 digitized measurements (Nipponbare cultivar)'
    },
    {
      author: 'Karavolias et al. (2024)',
      title: 'Promoter editing of OsSTOMAGEN tunes stomatal density and yield traits in rice',
      journal: 'Plant Biotechnology Journal',
      gene: 'OsSTOMAGEN Promoter Edit',
      doi: '10.1111/pbi.14464',
      url: 'https://doi.org/10.1111/pbi.14464',
      contrib: '123 digitized measurements (Kitaake cultivar)'
    }
  ];

  return (
    <section className="bg-white border border-agri-border rounded-2xl p-5 md:p-6 mb-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <BookOpen className="w-5 h-5 text-agri-deep" />
        <div>
          <h3 className="text-base font-extrabold text-agri-textDark">
            Source Research Papers
          </h3>
          <p className="text-xs text-agri-textMuted font-medium">
            100% Peer-Reviewed Experimental Foundations (168 Digitized Biological Measurements)
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {papers.map((paper, idx) => (
          <motion.a
            key={paper.doi}
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: idx * 0.08 }}
            whileHover={{ y: -3, scale: 1.01 }}
            className="bg-agri-cardSoft border border-agri-border border-l-4 border-l-agri-deep rounded-xl p-4 flex flex-col justify-between hover:border-agri-deep hover:shadow-[0_6px_20px_rgba(46,125,50,0.12)] transition-all group"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="px-2 py-0.5 rounded-md bg-agri-sageLight border border-agri-sageBorder text-agri-deep text-[11px] font-extrabold flex items-center gap-1">
                  <Dna className="w-3 h-3 text-agri-leaf" />
                  <span>{paper.gene}</span>
                </span>
                <ExternalLink className="w-4 h-4 text-agri-textMuted group-hover:text-agri-deep group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </div>

              <h4 className="text-xs font-black text-agri-textDark mb-1 group-hover:text-agri-deep transition-colors leading-snug">
                {paper.author}
              </h4>
              <p className="text-xs text-agri-textMuted font-semibold line-clamp-2 mb-2 italic">
                "{paper.title}"
              </p>
            </div>

            <div className="pt-2 border-t border-agri-border/60 flex items-center justify-between text-[11px]">
              <span className="font-bold text-agri-leaf">{paper.journal}</span>
              <span className="text-agri-textMuted font-mono font-medium">DOI: {paper.doi}</span>
            </div>
          </motion.a>
        ))}
      </div>
    </section>
  );
}
