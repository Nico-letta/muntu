import React, { memo } from 'react';
import { motion } from 'framer-motion';
import type { Variants } from 'framer-motion';
import { Target, Zap, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import CustomActionButton from '../ui/CustomActionButton';

// 1. Constantes typées et gelées pour éviter la ré-allocation mémoire
const TEAM_AVATARS = [
  '/IMG_5174.webp',
  '/IMG_5182.webp', 
  '/IMG_5199.webp',
  '/IMG_5216.webp'
] as const;

// 2. Variants optimisés (Utilisation de hardware acceleration via transform)
const fadeInDown: Variants = {
  hidden: { opacity: 0, y: 20 }, // Réduit de 40 à 20 pour éviter les grands sauts de layout sur mobile
  visible: { 
    opacity: 1, 
    y: 0, 
    transition: { 
      duration: 0.5, // 0.8 est trop lent sur mobile (sensation de lourdeur)
      ease: [0.215, 0.610, 0.355, 1.000] // Cubic-bezier optimisé pour l'UI (EaseOutCubic)
    } 
  }
};

const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { 
      staggerChildren: 0.1, 
      delayChildren: 0.1 
    }
  }
};

// Option de viewport globale pour économiser la batterie (Exécuté une seule fois)
const VIEWPORT_CONFIG = { once: true, margin: "-10%" };

const AboutSection: React.FC = () => {
  const navigate = useNavigate();

  return (
    <section className="relative w-full py-16 md:py-24 lg:py-32 overflow-hidden bg-[var(--color-brand-light)] font-sans contain-intrinsic-size">
      
      {/* --- ÉLÉMENTS DÉCORATIFS (Désactivés ou simplifiés sur mobile pour économiser le GPU) --- */}
      <motion.div 
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 0.05 }}
        viewport={VIEWPORT_CONFIG}
        transition={{ duration: 1 }}
        className="absolute top-0 right-0 w-1/3 h-full bg-[var(--color-brand-lavender)] z-0 pointer-events-none will-change-opacity hidden sm:block" 
      />
      
      {/* Background Text : purement décoratif, masqué sur mobile pour éviter la surcharge de layout textuel */}
      <div className="absolute top-1/2 left-6 -translate-y-1/2 opacity-[0.02] pointer-events-none hidden xl:block z-0">
        <motion.h2 
          initial={{ x: -50, opacity: 0 }}
          whileInView={{ x: 0, opacity: 1 }}
          viewport={VIEWPORT_CONFIG}
          transition={{ duration: 1.2, ease: "easeOut" }}
          className="text-[12vw] font-black text-[var(--color-brand-dark)] leading-none uppercase select-none tracking-tighter will-change-transform"
        >
          Corporate
        </motion.h2>
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-12 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-24 items-center">
          
          {/* --- COLONNE GAUCHE : VISUEL (Optimisé Desktop vs Mobile) --- */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={VIEWPORT_CONFIG}
            transition={{ duration: 0.6 }}
            className="col-span-1 lg:col-span-5 relative group"
          >
            {/* Cadre de structure : animation désactivée au hover sur mobile (no-hover query) */}
            <div className="absolute -top-4 -right-4 md:-top-6 md:-right-6 w-full h-full border-2 border-[var(--color-brand-blue)] z-0 transform transition-transform duration-500 group-hover:translate-x-2 group-hover:-translate-y-2 motion-reduce:transition-none" />

            {/* Container Image Principal avec Ratio strict pour éviter le CLS */}
            <div className="relative z-10 w-full aspect-[3/4] bg-[var(--color-brand-dark)] overflow-hidden border border-[var(--color-brand-dark)] shadow-sm">
              <img 
                src="/hero-display.jpg" 
                alt="L'équipe" 
                loading="lazy"
                decoding="async"
                className="w-full h-full object-cover grayscale transition-transform duration-700 ease-out md:group-hover:scale-105 md:group-hover:grayscale-0 will-change-transform"
              />
              <div className="absolute inset-0 bg-[var(--color-brand-blue)] mix-blend-multiply opacity-0 md:group-hover:opacity-20 transition-opacity duration-500 pointer-events-none" />
            </div>

            {/* Badge d'Impact (Style Brutaliste) */}
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={VIEWPORT_CONFIG}
              transition={{ delay: 0.2, type: "spring", damping: 20 }}
              className="absolute -bottom-6 -left-2 sm:-bottom-10 sm:left-4 lg:-left-10 z-20 bg-[var(--color-brand-lime)] p-4 sm:p-6 lg:p-8 shadow-[8px_8px_0px_rgba(21,22,50,1)] sm:shadow-[15px_15px_0px_rgba(21,22,50,1)]"
            >
              <div className="flex flex-col gap-1">
                <span className="text-3xl sm:text-4xl lg:text-5xl font-black text-[var(--color-brand-dark)] leading-none">08+</span>
                <span className="text-[9px] sm:text-[10px] font-black uppercase tracking-[0.2em] text-[var(--color-brand-dark)] leading-tight">
                  Ans d'Expertise <br/> Radicales
                </span>
              </div>
            </motion.div>
          </motion.div>

          {/* --- COLONNE DROITE : CONTENU CONTRAINT --- */}
          <motion.div 
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={VIEWPORT_CONFIG}
            className="col-span-1 lg:col-span-7 mt-8 lg:mt-0"
          >
            {/* Label */}
            <motion.div variants={fadeInDown} className="flex items-center gap-4 mb-4 sm:mb-6">
              <div className="h-[2px] w-8 sm:w-12 bg-[var(--color-brand-blue)]" />
              <span className="text-[10px] sm:text-xs font-black uppercase tracking-[0.3em] text-[var(--color-brand-blue)]">
                Qui nous sommes
              </span>
            </motion.div>

            {/* Titre Fluide */}
            <motion.h2 variants={fadeInDown} className="text-3xl sm:text-5xl lg:text-7xl font-black text-[var(--color-brand-dark)] leading-[0.95] uppercase mb-6 sm:mb-8 tracking-tighter">
              Stratégie, Contenu <span className="block sm:inline lg:block">Et Influence</span>
              <span className="block text-transparent style-stroke" style={{ WebkitTextStroke: '1px var(--color-brand-dark)' }}>
                Au Service De Votre Image
              </span>
            </motion.h2>

            {/* Paragraphes avec Surlignage Performance-First */}
            <motion.p variants={fadeInDown} className="text-lg sm:text-xl lg:text-2xl text-[var(--color-brand-dark)] font-medium leading-tight mb-8 max-w-xl">
              Notre collectif accompagne les marques dans la construction d’une{' '}
              <span className="relative inline-block isolate">
                <span className="relative z-10 italic pr-1">communication claire</span>
                <motion.span 
                  initial={{ scaleX: 0 }}
                  whileInView={{ scaleX: 1 }}
                  viewport={VIEWPORT_CONFIG}
                  transition={{ delay: 0.5, duration: 0.4 }}
                  className="absolute bottom-0.5 left-0 w-full h-2 sm:h-3 bg-[var(--color-brand-lime)] -z-10 origin-left will-change-transform"
                />
              </span>{' '}
              forte et durable.
            </motion.p>

            {/* Stats Grille */}
            <motion.div variants={fadeInDown} className="grid grid-cols-1 sm:grid-cols-2 gap-6 sm:gap-8 mb-8 sm:mb-12 border-y border-[var(--color-brand-dark)]/10 py-6 sm:py-10">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-[var(--color-brand-lavender)]/20 border border-[var(--color-brand-blue)]/10 flex-shrink-0" aria-hidden="true">
                  <Target size={20} className="text-[var(--color-brand-blue)]" />
                </div>
                <div>
                  <h3 className="font-black uppercase text-[10px] sm:text-[11px] tracking-widest text-[var(--color-brand-dark)] mb-1">Notre Cible</h3>
                  <p className="text-xs sm:text-sm text-gray-500 font-medium leading-snug">Entreprises, institutions et marques</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="p-3 bg-[var(--color-brand-lime)]/20 border border-[var(--color-brand-dark)]/5 flex-shrink-0" aria-hidden="true">
                  <Zap size={20} className="text-[var(--color-brand-dark)]" />
                </div>
                <div>
                  <h3 className="font-black uppercase text-[10px] sm:text-[11px] tracking-widest text-[var(--color-brand-dark)] mb-1">Notre Force</h3>
                  <p className="text-xs sm:text-sm text-gray-500 font-medium leading-snug">Expertise stratégique & créativité audacieuse</p>
                </div>
              </div>
            </motion.div>

            {/* CTA & Team Avatars */}
            <motion.div variants={fadeInDown} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-6 sm:gap-8">
              <div className="flex-grow-0">
                <CustomActionButton
                  label={
                    <span className="flex items-center justify-center gap-2 font-bold text-xs sm:text-sm tracking-wider">
                      EXPLORER LE MANIFESTO <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
                    </span>
                  }
                  backgroundColor={'var(--color-brand-dark)'}
                  borderColor={'var(--color-brand-dark)'}
                  textColor={'var(--color-brand-lime)'}
                  onClick={() => navigate('/#manifesto')}
                />
              </div>
              
              <div className="flex items-center gap-4 justify-start sm:justify-auto mt-2 sm:mt-0">
                <div className="flex -space-x-2.5 sm:-space-x-3">
                  {TEAM_AVATARS.map((avatarSrc, i) => (
                    <div 
                      key={avatarSrc}
                      className="w-10 h-10 sm:w-12 sm:h-12 rounded-full border-2 border-[var(--color-brand-light)] bg-gray-100 overflow-hidden shadow-sm transition-transform duration-300 md:hover:-translate-y-1 md:hover:z-30 cursor-pointer"
                    >
                      <img
                        src={avatarSrc}
                        alt={`Membre de l'équipe ${i + 1}`}
                        width={48}
                        height={48}
                        loading="lazy"
                        decoding="async"
                        className="object-cover w-full h-full"
                      />
                    </div>
                  ))}
                </div>
                <span className="text-[10px] sm:text-[11px] font-black uppercase tracking-tighter leading-tight text-[var(--color-brand-dark)]">
                  Expertise <br/> Collective
                </span>
              </div>
            </motion.div>

          </motion.div>
        </div>
      </div>
    </section>
  );
};

// 3. Memoization inutile (Anti-pattern sans props fluctuantes)
export default memo(AboutSection);